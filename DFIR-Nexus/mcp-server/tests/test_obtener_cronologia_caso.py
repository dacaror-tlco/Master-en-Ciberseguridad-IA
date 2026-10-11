"""
Tests de la tool `obtener_cronologia_caso` (Fase 2C, Timeline).

`GET /timeline/cases/{case_id}` (timeline/app/modules/timeline/routes.py)
nunca comprueba si el caso existe de verdad — solo lee `timeline_events`
para ese case_id y devuelve lo que haya, vacío o no. Por eso esta tool
nunca puede devolver "no_encontrado": no hay forma de distinguirlo de
"caso real sin cronología" desde este endpoint. Verificado leyendo el
código real del backend, no asumido.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import obtener_cronologia_caso

TIMELINE_BASE_URL = "http://localhost:8002"
CASOS_BASE_URL = "http://localhost:8000"

_EVENTOS_DE_EJEMPLO = [
    {
        "id": 1,
        "case_id": 8,
        "fecha_hora": "2026-09-02T20:15:00",
        "descripcion": "log: access.log de Apache subido",
        "origen_modulo": "evidence",
        "origen_id": 5,
        "orden": 1,
    },
    {
        "id": 2,
        "case_id": 8,
        "fecha_hora": "2026-09-02T21:00:00",
        "descripcion": "Autenticación fallida detectada",
        "origen_modulo": "tracking",
        "origen_id": 12,
        "orden": 2,
    },
]


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- argumento inválido ------------------------------------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_timeline():
    with pytest.raises(ToolError, match="entero positivo"):
        await obtener_cronologia_caso(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await obtener_cronologia_caso(-2)


# --- respuesta correcta ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_cronologia_con_eventos_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(
        return_value=httpx.Response(200, json=_EVENTOS_DE_EJEMPLO)
    )

    resultado = await obtener_cronologia_caso(8)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 2
    assert resultado["datos"]["eventos"] == _EVENTOS_DE_EJEMPLO


# --- cronología sin eventos (el backend lo representa como lista vacía) ----


@pytest.mark.asyncio
@respx.mock
async def test_cronologia_sin_eventos_es_sin_resultados():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(return_value=httpx.Response(200, json=[]))

    resultado = await obtener_cronologia_caso(8)

    assert resultado["estado"] == "sin_resultados"
    assert "detalle" in resultado


# --- la petición va al backend correcto (Timeline, no Casos) ---------------


@pytest.mark.asyncio
@respx.mock
async def test_la_peticion_de_datos_va_a_timeline_no_a_casos():
    _mockear_login_ok()
    ruta = respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(
        return_value=httpx.Response(200, json=[])
    )

    await obtener_cronologia_caso(8)

    assert ruta.called
    assert ruta.calls.last.request.headers["authorization"] == "Bearer token-de-prueba"


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
    peticion = respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_EVENTOS_DE_EJEMPLO),
        ]
    )

    resultado = await obtener_cronologia_caso(8)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await obtener_cronologia_caso(8)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await obtener_cronologia_caso(8)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await obtener_cronologia_caso(8)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await obtener_cronologia_caso(8)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TIMELINE_BASE_URL}/timeline/cases/8").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await obtener_cronologia_caso(8)


# -----------------------------------------------------------------------------
# Prueba real contra Timeline local (SIN mocks). Se salta si no hay
# credenciales en el entorno, o si Casos/Timeline no responden.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_timeline_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    try:
        resultado = await obtener_cronologia_caso(8)
    except ToolError as exc:
        pytest.skip(f"Timeline no disponible en {TIMELINE_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] in ("ok", "sin_resultados")
