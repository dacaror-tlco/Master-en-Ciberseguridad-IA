"""
Tests de la tool `consultar_hallazgo_osint` (Fase 2E, OSINT).

A diferencia de `listar_hallazgos_osint`, `GET /osint-findings/{id}` SÍ
comprueba existencia real (`if finding is None: raise HTTPException(404,
...)` en el backend), así que sí distingue correctamente "no_encontrado".
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import consultar_hallazgo_osint

OSINT_BASE_URL = "http://localhost:8124"
CASOS_BASE_URL = "http://localhost:8000"

_HALLAZGO_DE_EJEMPLO = {
    "id": 4,
    "case_type": "ip",
    "source_table": "ip_cases",
    "source_id": 4,
    "case_id": 8,
    "subject_type": "ip_address",
    "subject_value": "203.0.113.45",
    "risk_score": 82,
    "risk_level": "high",
    "headline": "IP marcada en listas negras",
    "flag_count": 3,
    "analyzed_at": "2026-09-03T09:22:01",
    "created_at": "2026-09-03T09:22:01",
    "top_flags": ["blacklist_abuseipdb", "blacklist_virustotal"],
    "details": {"country": "RU", "isp": "Ejemplo Hosting"},
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- validación de argumentos -----------------------------------------------


@pytest.mark.asyncio
async def test_finding_id_no_positivo_se_rechaza_sin_llamar_a_osint():
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_hallazgo_osint(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_hallazgo_osint(-4)


# --- respuesta correcta ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_hallazgo_encontrado_devuelve_los_datos_reales_incluido_detalle():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(
        return_value=httpx.Response(200, json=_HALLAZGO_DE_EJEMPLO)
    )

    resultado = await consultar_hallazgo_osint(4)

    assert resultado == {"estado": "ok", "datos": _HALLAZGO_DE_EJEMPLO}
    assert "top_flags" in resultado["datos"]
    assert "details" in resultado["datos"]


# --- no encontrado -----------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_hallazgo_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/999").mock(
        return_value=httpx.Response(404, json={"detail": "No existe el finding 999"})
    )

    resultado = await consultar_hallazgo_osint(999)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe el finding 999"}


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
    peticion = respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_HALLAZGO_DE_EJEMPLO),
        ]
    )

    resultado = await consultar_hallazgo_osint(4)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await consultar_hallazgo_osint(4)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(
        return_value=httpx.Response(422, json={"detail": "id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await consultar_hallazgo_osint(4)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await consultar_hallazgo_osint(4)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await consultar_hallazgo_osint(4)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await consultar_hallazgo_osint(4)


# -----------------------------------------------------------------------------
# Prueba real contra OSINT local (SIN mocks). Se salta si no hay credenciales,
# si OSINT no responde, o si no hay ningún hallazgo real todavía — reutiliza
# listar_hallazgos_osint para encontrar un finding_id real sin fabricar uno.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_osint_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    from app.main import listar_hallazgos_osint

    try:
        lista = await listar_hallazgos_osint(limit=1)
    except ToolError as exc:
        pytest.skip(f"OSINT no disponible en {OSINT_BASE_URL}, o credenciales rechazadas: {exc}")

    if lista["estado"] != "ok":
        pytest.skip("No hay ningún hallazgo OSINT real con el que probar consultar_hallazgo_osint.")

    finding_id = lista["datos"]["hallazgos"][0]["id"]
    resultado = await consultar_hallazgo_osint(finding_id)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["id"] == finding_id
