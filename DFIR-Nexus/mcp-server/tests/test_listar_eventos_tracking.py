"""
Tests de la tool `listar_eventos_tracking` (Fase 2D, Tracking).

`GET /cases/{case_id}/tracking/events` (track-inc/app/modules/tracking/
routes.py) SÍ comprueba existencia real del caso (levanta
`service.CaseNotFoundError` -> 404), a diferencia de Timeline/Informes en
la Fase 2C — verificado leyendo el código real, no asumido. Admite
paginación real (`skip`, `limit`, con los mismos límites que el backend:
`limit` entre 1 y 1000).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import listar_eventos_tracking

TRACKING_BASE_URL = "http://localhost:8001"
CASOS_BASE_URL = "http://localhost:8000"

_EVENTOS_DE_EJEMPLO = [
    {
        "id": 22,
        "case_id": 8,
        "hora": "2026-09-03T00:21:57Z",
        "evento": "Detección de escaneo de puertos",
        "severidad": "media",
        "fuente_log": "firewall",
        "usuario_detectado": "admin",
        "regla": "escaneo_puertos",
        "hora_inferida": False,
    },
    {
        "id": 23,
        "case_id": 8,
        "hora": "2026-09-03T02:21:57Z",
        "evento": "Intento de acceso fallido por SSH",
        "severidad": "alta",
        "fuente_log": "auth.log",
        "usuario_detectado": "root",
        "regla": "autenticacion_fallida",
        "hora_inferida": False,
    },
]


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- validación de argumentos -----------------------------------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_tracking():
    with pytest.raises(ToolError, match="entero positivo"):
        await listar_eventos_tracking(0)


@pytest.mark.asyncio
async def test_skip_negativo_se_rechaza():
    with pytest.raises(ToolError, match="skip"):
        await listar_eventos_tracking(8, skip=-1)


@pytest.mark.asyncio
async def test_limit_fuera_de_rango_se_rechaza():
    with pytest.raises(ToolError, match="limit"):
        await listar_eventos_tracking(8, limit=0)
    with pytest.raises(ToolError, match="limit"):
        await listar_eventos_tracking(8, limit=1001)


# --- respuesta correcta ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_eventos_encontrados_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(200, json=_EVENTOS_DE_EJEMPLO)
    )

    resultado = await listar_eventos_tracking(8)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 2
    assert resultado["datos"]["eventos"] == _EVENTOS_DE_EJEMPLO
    assert resultado["datos"]["skip"] == 0
    assert resultado["datos"]["limit"] == 100


# --- paginación: valores por defecto, skip, limit ---------------------------


@pytest.mark.asyncio
@respx.mock
async def test_paginacion_por_defecto_envia_skip_0_limit_100():
    _mockear_login_ok()
    ruta = respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(200, json=[])
    )

    await listar_eventos_tracking(8)

    peticion = ruta.calls.last.request
    assert peticion.url.params["skip"] == "0"
    assert peticion.url.params["limit"] == "100"


@pytest.mark.asyncio
@respx.mock
async def test_paginacion_personalizada_se_envia_tal_cual():
    _mockear_login_ok()
    ruta = respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(200, json=[])
    )

    resultado = await listar_eventos_tracking(8, skip=50, limit=10)

    peticion = ruta.calls.last.request
    assert peticion.url.params["skip"] == "50"
    assert peticion.url.params["limit"] == "10"
    assert resultado["estado"] == "sin_resultados"


# --- vacío / no encontrado ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_sin_eventos_es_sin_resultados():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(return_value=httpx.Response(200, json=[]))

    resultado = await listar_eventos_tracking(8)

    assert resultado["estado"] == "sin_resultados"
    assert "detalle" in resultado


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/999/tracking/events").mock(
        return_value=httpx.Response(404, json={"detail": "Caso 999 no encontrado"})
    )

    resultado = await listar_eventos_tracking(999)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso 999 no encontrado"}


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
    peticion = respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_EVENTOS_DE_EJEMPLO),
        ]
    )

    resultado = await listar_eventos_tracking(8)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await listar_eventos_tracking(8)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(422, json={"detail": "parámetros inválidos"})
    )

    with pytest.raises(ToolError, match="422"):
        await listar_eventos_tracking(8)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await listar_eventos_tracking(8)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await listar_eventos_tracking(8)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await listar_eventos_tracking(8)


# -----------------------------------------------------------------------------
# Prueba real contra Tracking local (SIN mocks). Se salta si no hay
# credenciales en el entorno, si los backends no responden, o si ninguno de
# los casos de prueba conocidos tiene eventos de tracking reales.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_tracking_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    resultado = None
    for candidato in (1, 8, 18, 19, 20):
        try:
            intento = await listar_eventos_tracking(candidato)
        except ToolError as exc:
            pytest.skip(f"Tracking no disponible en {TRACKING_BASE_URL}, o credenciales rechazadas: {exc}")
        if intento["estado"] == "ok":
            resultado = intento
            break

    if resultado is None:
        pytest.skip("Ninguno de los casos de prueba conocidos tiene eventos de tracking reales.")

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] > 0
