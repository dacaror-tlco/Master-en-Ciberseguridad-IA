"""
Tests de la tool `registrar_evidencia` (Fase 2H, Casos).

`POST /cases/{case_id}/evidences` (backend/app/modules/cases/routes.py)
verificado en el código real:
- `EvidenceCreate`: `tipo`/`valor` obligatorios, `observaciones`/
  `fecha_adquisicion` opcionales. Sin validación propia de "no vacío" en
  el esquema — por eso esta tool valida tipo/valor no vacíos ANTES de
  llamar al backend.
- `tipo` es `VARCHAR(50)` en la tabla (`models.py::Evidence.tipo`): sin
  límite en el esquema Pydantic, así que MySQL truncaría o rechazaría
  silenciosamente un valor más largo si no se valida aquí — se valida
  ANTES de tocar la red.
- El hash de integridad (`hash_valor`, SHA-256 de `valor`) lo calcula el
  backend UNA sola vez al crear (`repository.py::create_evidence`,
  `integrity.py::calcular_hash_valor`) — esta tool nunca lo calcula ni lo
  envía, solo lee el que devuelve la respuesta real.
- 404: caso no encontrado. 409: caso eliminado lógicamente
  (`CaseDeletedError`) — verificado en el código que un caso ARCHIVADO
  SÍ admite evidencia nueva (`create_evidence` solo llama a
  `get_active_case`, que comprueba `eliminado`, nunca
  `estado == archivado`): no es una omisión de esta tool.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import registrar_evidencia

CASOS_BASE_URL = "http://localhost:8000"

_EVIDENCIA_CREADA = {
    "id": 17,
    "case_id": 8,
    "tipo": "imagen_disco",
    "valor": "sha1:abcdef...",
    "hash_valor": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "observaciones": None,
    "fecha_subida": "2026-09-29T10:00:00",
    "fecha_adquisicion": None,
    "fecha_actualizacion": "2026-09-29T10:00:00",
    "eliminado": False,
    "fecha_eliminacion": None,
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
        await registrar_evidencia(8, "imagen_disco", "sha1:abcdef...", confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="entero positivo"):
        await registrar_evidencia(0, "imagen_disco", "valor", confirmado=True)
    with pytest.raises(ToolError, match="entero positivo"):
        await registrar_evidencia(-1, "imagen_disco", "valor", confirmado=False)


@pytest.mark.asyncio
async def test_tipo_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="tipo"):
        await registrar_evidencia(8, "   ", "valor", confirmado=True)


@pytest.mark.asyncio
async def test_tipo_demasiado_largo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="50 caracteres"):
        await registrar_evidencia(8, "x" * 51, "valor", confirmado=True)


@pytest.mark.asyncio
async def test_valor_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="valor"):
        await registrar_evidencia(8, "imagen_disco", "   ", confirmado=True)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_registra_y_devuelve_los_datos_reales_con_hash():
    _mockear_login_ok()
    ruta = respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        return_value=httpx.Response(201, json=_EVIDENCIA_CREADA)
    )

    resultado = await registrar_evidencia(8, "imagen_disco", "sha1:abcdef...", confirmado=True)

    assert resultado == {"estado": "ok", "datos": _EVIDENCIA_CREADA}
    assert resultado["datos"]["hash_valor"]  # el hash viene del backend, no lo calcula esta tool
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {
        "tipo": "imagen_disco",
        "valor": "sha1:abcdef...",
        "observaciones": None,
        "fecha_adquisicion": None,
    }
    assert "hash_valor" not in cuerpo  # nunca lo calcula ni lo envía esta tool


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_con_observaciones_y_fecha_adquisicion_las_envia_tal_cual():
    _mockear_login_ok()
    ruta = respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        return_value=httpx.Response(201, json=_EVIDENCIA_CREADA)
    )

    resultado = await registrar_evidencia(
        8,
        "imagen_disco",
        "sha1:abcdef...",
        confirmado=True,
        observaciones="Adquirida con dd",
        fecha_adquisicion="2026-09-01T12:00:00",
    )

    assert resultado["estado"] == "ok"
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {
        "tipo": "imagen_disco",
        "valor": "sha1:abcdef...",
        "observaciones": "Adquirida con dd",
        "fecha_adquisicion": "2026-09-01T12:00:00",
    }


# --- no encontrado -----------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/999/evidences").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await registrar_evidencia(999, "imagen_disco", "valor", confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso no encontrado"}


# --- conflicto (409) --------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_eliminado_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        return_value=httpx.Response(
            409, json={"detail": "El caso está eliminado: no se pueden añadir evidencias"}
        )
    )

    resultado = await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)

    assert resultado == {
        "estado": "conflicto",
        "detalle": "El caso está eliminado: no se pueden añadir evidencias",
    }


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
    peticion = respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(201, json=_EVIDENCIA_CREADA),
        ]
    )

    resultado = await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(
        return_value=httpx.Response(422, json={"detail": "tipo inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases/8/evidences").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await registrar_evidencia(8, "imagen_disco", "valor", confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Casos local (SIN mocks). Crea su PROPIO caso de prueba
# (vía crear_caso, Fase 2G) y registra en él una evidencia de prueba REAL y
# claramente identificable, comprobando que el hash de integridad que
# devuelve el backend corresponde de verdad a `valor` (SHA-256), y que
# `verificar_integridad_evidencia` (Fase 2B) la confirma íntegra.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_casos_local_si_esta_disponible():
    import hashlib
    import os
    from datetime import datetime, timezone

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    from app.main import crear_caso, verificar_integridad_evidencia

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre_caso = f"MCP-TEST-Fase2H-registrar_evidencia-{marca}"
    valor = f"Evidencia de prueba MCP Fase2H {marca}"

    try:
        caso = await crear_caso(nombre_caso, "MCP Server (test automático)", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert caso["estado"] == "ok"
    case_id = caso["datos"]["id"]

    resultado = await registrar_evidencia(
        case_id,
        "nota_prueba_mcp",
        valor,
        confirmado=True,
        observaciones="Creada por tests/test_registrar_evidencia.py — segura de conservar o borrar.",
    )

    assert resultado["estado"] == "ok"
    datos = resultado["datos"]
    assert datos["case_id"] == case_id
    assert datos["tipo"] == "nota_prueba_mcp"
    assert datos["valor"] == valor
    assert datos["hash_valor"] == hashlib.sha256(valor.encode("utf-8")).hexdigest()

    integridad = await verificar_integridad_evidencia(case_id, datos["id"])
    assert integridad["estado"] == "ok"
    assert integridad["datos"]["integro"] is True

    print(
        f"\n[test_real_contra_casos_local_si_esta_disponible] Caso de prueba id={case_id} "
        f"nombre={nombre_caso!r}, evidencia id={datos['id']} registrada e íntegra."
    )
