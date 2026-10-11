"""
Tests de la tool `consultar_auditoria_caso` (Fase 2A).

Mismo criterio que los otros ficheros de tests: HTTP hacia Casos
interceptado con respx, `_sesion_sin_token` de conftest.py resetea el JWT
en memoria entre tests.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import consultar_auditoria_caso

CASOS_BASE_URL = "http://localhost:8000"


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- auditoría existente ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_auditoria_existente_devuelve_las_entradas_reales():
    _mockear_login_ok()
    entradas = [
        {
            "id": 10,
            "case_id": 1,
            "evidence_id": None,
            "accion": "case_creado",
            "actor": "api",
            "detalle": None,
            "creado_en": "2026-01-01T00:00:00",
        },
        {
            "id": 11,
            "case_id": 1,
            "evidence_id": None,
            "accion": "case_estado_cambiado",
            "actor": "api",
            "detalle": {"de": "abierto", "a": "en_progreso"},
            "creado_en": "2026-01-05T00:00:00",
        },
    ]
    respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(return_value=httpx.Response(200, json=entradas))

    resultado = await consultar_auditoria_caso(1)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["entradas"] == entradas


@pytest.mark.asyncio
@respx.mock
async def test_caso_sin_historial_devuelve_lista_vacia_no_error():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(return_value=httpx.Response(200, json=[]))

    resultado = await consultar_auditoria_caso(1)

    assert resultado == {"estado": "ok", "datos": {"entradas": []}}


# --- caso inexistente (404) -------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_no_es_error_es_resultado_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/999/auditoria").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await consultar_auditoria_caso(999)

    assert resultado == {
        "estado": "no_encontrado",
        "detalle": "No existe ningún caso con id=999 en Nexus.",
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
    peticion = respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=[]),
        ]
    )

    resultado = await consultar_auditoria_caso(1)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await consultar_auditoria_caso(1)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await consultar_auditoria_caso(1)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/1/auditoria").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await consultar_auditoria_caso(1)


# --- error de conexión ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await consultar_auditoria_caso(1)


# --- case_id <= 0 ---------------------------------------------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_auditoria_caso(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await consultar_auditoria_caso(-5)


# -----------------------------------------------------------------------------
# Prueba real contra el backend de Casos local (SIN mocks). Se salta si no hay
# credenciales en el entorno, o si Casos no responde — nunca hardcodeadas
# aquí, y nunca crea/modifica nada: solo lee /cases/1/auditoria (caso ya
# existente, "Caso de prueba Módulo 4").
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_casos_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    try:
        resultado = await consultar_auditoria_caso(1)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] in ("ok", "no_encontrado")
