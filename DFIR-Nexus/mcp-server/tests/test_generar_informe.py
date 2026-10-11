"""
Tests de la tool `generar_informe` (Fase 2H, Informes) — la tool de
escritura con COSTE ECONÓMICO REAL (llamada a un modelo de IA) de esta
fase.

`POST /reports/generate` (sharingan/app/modules/reports/routes.py)
verificado en el código real: body `ReportGenerateRequest` (`case_id`,
`generado_por`, `notas?`, `opciones?`). Esta tool NO expone `opciones`
(alcance parcial: anexos/formatos/fechas) — omitirlo, que es justo lo que
hace esta tool, emite el informe COMPLETO (todos los anexos, los cuatro
formatos), el comportamiento por defecto documentado por el propio
backend.

Errores reales verificados en el código:
- 404 `CaseNotFoundError`: el caso no existe.
- 422 `EmptyTimelineError`/`EmptySelectionError`: el caso no tiene
  cronología calculada todavía, o el alcance pedido deja la cronología
  vacía — se propagan por el camino genérico de `_peticion_segura`
  (ya incluye el `detail` real en el mensaje).
- 409 `VersionConflictError`: dos generaciones simultáneas del mismo caso
  se pisaron el número de versión — el propio backend documenta que
  reintentar basta.
- 503 `AIConfigError`/`AIUnavailableError`, 502 `AIResponseError`: fallos
  relacionados con la IA — caen en el camino genérico de `_peticion_segura`
  para códigos >=500, que desde esta fase también incluye el `detail` real
  del backend en el mensaje (antes solo lo hacía para 422).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import generar_informe

INFORMES_BASE_URL = "http://localhost:8003"
CASOS_BASE_URL = "http://localhost:8000"

_INFORME_GENERADO = {
    "id": 5,
    "case_id": 8,
    "fecha_generacion": "2026-09-29T10:00:00",
    "resumen_ia": "Resumen generado por IA...",
    "archivo_pdf": "case_8/report_v2.pdf",
    "generado_por": "MCP Server (test automático)",
    "version": 2,
    "notas": None,
    "huellas": {"pdf": "abc123...", "prompt": "def456..."},
    "opciones": None,
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- confirmado=False no realiza NINGUNA petición HTTP ----------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_false_no_hace_ninguna_peticion_http():
    with pytest.raises(ToolError, match="confirmado=true"):
        await generar_informe(8, "Yolanda", confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="entero positivo"):
        await generar_informe(0, "Yolanda", confirmado=True)


@pytest.mark.asyncio
async def test_generado_por_vacio_o_demasiado_largo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="generado_por"):
        await generar_informe(8, "   ", confirmado=True)
    with pytest.raises(ToolError, match="100 caracteres"):
        await generar_informe(8, "x" * 101, confirmado=True)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_genera_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    ruta = respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(200, json=_INFORME_GENERADO)
    )

    resultado = await generar_informe(8, "Yolanda", confirmado=True)

    assert resultado == {"estado": "ok", "datos": _INFORME_GENERADO}
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {"case_id": 8, "generado_por": "Yolanda", "notas": None}
    assert "opciones" not in cuerpo  # nunca la envía: emite el informe completo por defecto


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_con_notas_las_envia_tal_cual():
    _mockear_login_ok()
    ruta = respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(200, json=_INFORME_GENERADO)
    )

    resultado = await generar_informe(8, "Yolanda", confirmado=True, notas="Prioriza el anexo de tracking")

    assert resultado["estado"] == "ok"
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo["notas"] == "Prioriza el anexo de tracking"


# --- no encontrado -----------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(404, json={"detail": "No existe el caso 999"})
    )

    resultado = await generar_informe(999, "Yolanda", confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe el caso 999"}


# --- conflicto (409) --------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_conflicto_de_version_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(
            409, json={"detail": "Conflicto de versión al generar el informe; reintenta la petición."}
        )
    )

    resultado = await generar_informe(8, "Yolanda", confirmado=True)

    assert resultado["estado"] == "conflicto"
    assert "reintenta" in resultado["detalle"]


# --- 401 + reautenticación ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_401_reautentica_una_vez_y_repite_la_peticion():
    login = respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "token-viejo", "token_type": "bearer", "expires_in": 7200}),
            httpx.Response(200, json={"access_token": "token-nuevo", "token_type": "bearer", "expires_in": 7200}),
        ]
    )
    peticion = respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_INFORME_GENERADO),
        ]
    )

    resultado = await generar_informe(8, "Yolanda", confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await generar_informe(8, "Yolanda", confirmado=True)


# --- 422 (negocio: sin cronología / selección vacía) -----------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_sin_cronologia_se_propaga_con_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(
            422, json={"detail": "El caso no tiene cronología calculada todavía."}
        )
    )

    with pytest.raises(ToolError, match="cronología calculada"):
        await generar_informe(8, "Yolanda", confirmado=True)


# --- 5xx (incluye 502/503 relacionados con la IA) ---------------------------


@pytest.mark.asyncio
@respx.mock
async def test_503_ia_no_disponible_incluye_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(503, json={"detail": "El proveedor de IA no está disponible ahora mismo."})
    )

    with pytest.raises(ToolError, match="proveedor de IA no está disponible"):
        await generar_informe(8, "Yolanda", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_502_respuesta_ia_no_firmable_incluye_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(
        return_value=httpx.Response(502, json={"detail": "La IA citó un evento que no existe en la cronología."})
    )

    with pytest.raises(ToolError, match="citó un evento"):
        await generar_informe(8, "Yolanda", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_5xx_generico_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await generar_informe(8, "Yolanda", confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await generar_informe(8, "Yolanda", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{INFORMES_BASE_URL}/reports/generate").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await generar_informe(8, "Yolanda", confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Informes local (SIN mocks). ÚNICAMENTE con
# confirmado=True, como pide el enunciado — esta prueba tiene coste
# económico real (llamada a IA). Reutiliza el caso real #8 (ya usado por
# recalcular_cronologia en la Fase 2F, con cronología calculada) en vez de
# crear un caso de prueba propio: un caso recién creado sin evidencias ni
# cronología dispararía el 422 real de "sin cronología", no probaría el
# camino de éxito. Documenta el id/versión del informe generado.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_informes_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    try:
        resultado = await generar_informe(
            8,
            "MCP Server (test automático, Fase 2H)",
            confirmado=True,
            notas="Generado por tests/test_generar_informe.py — coste real de IA asumido a propósito.",
        )
    except ToolError as exc:
        pytest.skip(f"Informes no disponible en {INFORMES_BASE_URL}, o credenciales/IA rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    datos = resultado["datos"]
    assert datos["case_id"] == 8
    assert datos["resumen_ia"]

    print(
        f"\n[test_real_contra_informes_local_si_esta_disponible] Informe real generado: "
        f"id={datos['id']} case_id=8 version={datos['version']} — COSTE ECONÓMICO REAL asumido "
        f"(llamada a IA)."
    )
