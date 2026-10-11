"""
Tests del MVP del MCP Server: la tool `consultar_caso` y la capa de
autenticación de la que depende (app/core/auth.py).

Los backends reales de Nexus no intervienen en la mayoría de estos tests
— todo el HTTP hacia Casos se intercepta con respx. Al final del fichero
hay, además, una prueba que sí habla con el backend de Casos real si está
disponible (ver ese bloque para cómo se salta si no lo está).

Ejecución: desde mcp-server/, con
    venv/bin/python -m pytest
(usar "python -m pytest", no el script "pytest" a secas: así el propio
intérprete añade este directorio a sys.path y "import app..." resuelve
sin necesidad de instalar el paquete ni añadir un pytest.ini.)
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import consultar_caso

CASOS_BASE_URL = "http://localhost:8000"

# El fixture `_sesion_sin_token` (reset de casos_session entre tests) vive
# en tests/conftest.py, compartido por los tres ficheros de tests de
# tools — se aplica automáticamente (autouse) sin importarlo aquí.


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- 1 + 2: construcción de la petición HTTP y cabecera Authorization -------


@pytest.mark.asyncio
@respx.mock
async def test_peticion_incluye_metodo_ruta_y_authorization_header():
    _mockear_login_ok(token="abc123")
    ruta_caso = respx.get(f"{CASOS_BASE_URL}/cases/7").mock(
        return_value=httpx.Response(200, json={"id": 7, "nombre": "Caso de prueba"})
    )

    await consultar_caso(7)

    peticion = ruta_caso.calls.last.request
    assert peticion.method == "GET"
    assert peticion.url.path == "/cases/7"
    assert peticion.headers["authorization"] == "Bearer abc123"


# --- 3: caso encontrado ------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_encontrado_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "nombre": "Intrusión servidor web",
                "estado": "abierto",
                "responsable": "Yolanda",
                "descripcion": None,
                "fecha_creacion": "2026-01-01T00:00:00",
                "fecha_actualizacion": "2026-01-01T00:00:00",
                "eliminado": False,
                "fecha_eliminacion": None,
            },
        )
    )

    resultado = await consultar_caso(7)

    assert resultado["encontrado"] is True
    assert resultado["caso"]["id"] == 7
    assert resultado["caso"]["nombre"] == "Intrusión servidor web"


# --- 4: 404 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_no_encontrado_no_se_inventa_nada():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/999").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await consultar_caso(999)

    assert resultado == {
        "encontrado": False,
        "case_id": 999,
        "mensaje": "No existe ningún caso con id=999 en Nexus.",
    }


# --- 5: 401 + reautenticación (el segundo intento sí funciona) --------------


@pytest.mark.asyncio
@respx.mock
async def test_401_reautentica_una_vez_y_repite_la_peticion():
    login = respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "token-viejo", "token_type": "bearer", "expires_in": 7200}),
            httpx.Response(200, json={"access_token": "token-nuevo", "token_type": "bearer", "expires_in": 7200}),
        ]
    )
    peticion_caso = respx.get(f"{CASOS_BASE_URL}/cases/7").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json={"id": 7, "nombre": "Caso de prueba"}),
        ]
    )

    resultado = await consultar_caso(7)

    assert resultado["encontrado"] is True
    assert login.call_count == 2  # login inicial + reautenticación tras el 401
    assert peticion_caso.call_count == 2  # intento que dio 401 + repetición
    assert peticion_caso.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- 6: segundo 401 (tras reautenticar, Casos sigue rechazando) -------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/7").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await consultar_caso(7)


# --- 7: error de conexión (Casos inalcanzable) ------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await consultar_caso(7)


# --- 8: validación de case_id (antes de tocar la red) -----------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_caso(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_caso(-3)


# --- Extra: 422 (error controlado adicional pedido explícitamente) ---------


@pytest.mark.asyncio
@respx.mock
async def test_422_de_casos_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/7").mock(
        return_value=httpx.Response(422, json={"detail": [{"msg": "value is not a valid integer"}]})
    )

    with pytest.raises(ToolError, match="422"):
        await consultar_caso(7)


# -----------------------------------------------------------------------------
# Prueba real contra el backend de Casos local (SIN mocks).
#
# Se salta automáticamente si no hay credenciales de un usuario de servicio
# real en el entorno (nunca hardcodeadas aquí), o si Casos no responde en
# CASOS_BASE_URL. Comprueba, sin ningún doble de por medio, que esta capa
# habla de verdad con el backend real — la demostración de integración MCP
# end-to-end en sí (Claude Code invocando la tool) se hace aparte, fuera de
# pytest, tal y como se pide explícitamente en esta tarea.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_casos_local_si_esta_disponible():
    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    try:
        resultado = await consultar_caso(1)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert "encontrado" in resultado
