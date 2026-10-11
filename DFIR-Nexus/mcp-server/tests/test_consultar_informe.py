"""
Tests de la tool `consultar_informe` (Fase 2C, Informes).

A diferencia de `listar_informes_de_caso`, `GET /reports/{report_id}` SÍ
comprueba existencia real (`sharingan/app/modules/reports/routes.py`:
`if report is None: raise HTTPException(404, ...)`), así que esta tool sí
puede devolver "no_encontrado" de forma fiable.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import consultar_informe

INFORMES_BASE_URL = "http://localhost:8003"
CASOS_BASE_URL = "http://localhost:8000"

_INFORME_DE_EJEMPLO = {
    "id": 1,
    "case_id": 8,
    "fecha_generacion": "2026-09-10T12:00:00",
    "resumen_ia": "HALLAZGOS\n\n...\n\nCONCLUSIONES\n\n...",
    "archivo_pdf": "case_8/report_v1.pdf",
    "generado_por": "Yolanda",
    "version": 1,
    "notas": None,
    "huellas": {"pdf": "a" * 64},
    "opciones": None,
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- argumento inválido ------------------------------------------------


@pytest.mark.asyncio
async def test_report_id_no_positivo_se_rechaza_sin_llamar_a_informes():
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_informe(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_informe(-1)


# --- consulta correcta de un informe ----------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_informe_encontrado_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(return_value=httpx.Response(200, json=_INFORME_DE_EJEMPLO))

    resultado = await consultar_informe(1)

    assert resultado == {"estado": "ok", "datos": _INFORME_DE_EJEMPLO}


def test_archivo_pdf_es_metadata_no_se_toca():
    """No es un test funcional de la tool: documenta la garantía de diseño.
    `consultar_informe` nunca abre ni lee `archivo_pdf` — solo reenvía el
    JSON del backend tal cual, así que ese campo llega a Claude como texto
    (una ruta), nunca como el contenido de un fichero."""
    assert "archivo_pdf" in _INFORME_DE_EJEMPLO
    assert isinstance(_INFORME_DE_EJEMPLO["archivo_pdf"], str)


# --- informe inexistente -------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_informe_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/999").mock(
        return_value=httpx.Response(404, json={"detail": "No existe el informe 999"})
    )

    resultado = await consultar_informe(999)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe el informe 999"}


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
    peticion = respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_INFORME_DE_EJEMPLO),
        ]
    )

    resultado = await consultar_informe(1)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await consultar_informe(1)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(
        return_value=httpx.Response(422, json={"detail": "id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await consultar_informe(1)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await consultar_informe(1)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await consultar_informe(1)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/reports/1").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await consultar_informe(1)


# -----------------------------------------------------------------------------
# Prueba real contra Informes local (SIN mocks). Se salta si no hay
# credenciales, si los backends no responden, o si ningún caso conocido
# tiene informes reales — reutiliza listar_informes_de_caso para encontrar
# un report_id real sin fabricar ninguno.
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

    from app.main import listar_informes_de_caso

    report_id = None
    for candidato in (1, 8, 18, 19, 20):
        try:
            lista = await listar_informes_de_caso(candidato)
        except ToolError as exc:
            pytest.skip(f"Informes no disponible en {INFORMES_BASE_URL}, o credenciales rechazadas: {exc}")
        if lista["estado"] == "ok":
            report_id = lista["datos"]["informes"][0]["id"]
            break

    if report_id is None:
        pytest.skip("Ninguno de los casos de prueba conocidos tiene informes reales con los que probar.")

    resultado = await consultar_informe(report_id)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["id"] == report_id
