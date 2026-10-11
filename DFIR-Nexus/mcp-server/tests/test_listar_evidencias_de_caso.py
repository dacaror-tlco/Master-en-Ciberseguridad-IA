"""
Tests de la tool `listar_evidencias_de_caso` (Fase 2B).

Mismo criterio que los ficheros de la Fase 2A: HTTP hacia Casos
interceptado con respx, `_sesion_sin_token` de conftest.py resetea el JWT
en memoria entre tests.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import listar_evidencias_de_caso

CASOS_BASE_URL = "http://localhost:8000"

_EVIDENCIAS_DE_EJEMPLO = [
    {
        "id": 1,
        "case_id": 5,
        "tipo": "log",
        "valor": "/var/log/auth.log del servidor comprometido",
        "observaciones": None,
        "fecha_adquisicion": None,
        "fecha_subida": "2026-01-01T00:00:00",
        "fecha_actualizacion": "2026-01-01T00:00:00",
        "hash_valor": "a" * 64,
        "eliminado": False,
        "fecha_eliminacion": None,
    },
    {
        "id": 2,
        "case_id": 5,
        "tipo": "correo",
        "valor": "Cabecera del email de phishing original",
        "observaciones": "Recibido por el usuario afectado",
        "fecha_adquisicion": "2025-12-30T00:00:00",
        "fecha_subida": "2026-01-01T00:05:00",
        "fecha_actualizacion": "2026-01-01T00:05:00",
        "hash_valor": "b" * 64,
        "eliminado": False,
        "fecha_eliminacion": None,
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
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="entero positivo"):
        await listar_evidencias_de_caso(0)
    with pytest.raises(ToolError, match="entero positivo"):
        await listar_evidencias_de_caso(-1)


# --- respuesta válida del backend ------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_evidencias_encontradas_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(
        return_value=httpx.Response(200, json=_EVIDENCIAS_DE_EJEMPLO)
    )

    resultado = await listar_evidencias_de_caso(5)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 2
    assert [e["id"] for e in resultado["datos"]["evidencias"]] == [1, 2]


# --- respuesta vacía (sin_resultados, distinto de no_encontrado) -----------


@pytest.mark.asyncio
@respx.mock
async def test_caso_sin_evidencias_es_sin_resultados_no_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(return_value=httpx.Response(200, json=[]))

    resultado = await listar_evidencias_de_caso(5)

    assert resultado["estado"] == "sin_resultados"
    assert "detalle" in resultado


# --- caso inexistente --------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/999/evidences").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await listar_evidencias_de_caso(999)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso no encontrado"}


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
    peticion = respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_EVIDENCIAS_DE_EJEMPLO),
        ]
    )

    resultado = await listar_evidencias_de_caso(5)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await listar_evidencias_de_caso(5)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await listar_evidencias_de_caso(5)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await listar_evidencias_de_caso(5)


# --- error de conexión/timeout ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await listar_evidencias_de_caso(5)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await listar_evidencias_de_caso(5)


# -----------------------------------------------------------------------------
# Prueba real contra el backend de Casos local (SIN mocks). Se salta si no hay
# credenciales en el entorno, o si Casos no responde — nunca hardcodeadas
# aquí, y nunca crea/modifica/borra nada: solo lee.
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

    # Caso #1 ("Caso de prueba Módulo 4") ya usado en las pruebas reales de
    # Fase 2A; se reutiliza el mismo, sin crear nada nuevo.
    try:
        resultado = await listar_evidencias_de_caso(1)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] in ("ok", "sin_resultados", "no_encontrado")
