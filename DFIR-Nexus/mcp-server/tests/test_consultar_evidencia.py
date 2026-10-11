"""
Tests de la tool `consultar_evidencia` (Fase 2B).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import consultar_evidencia

CASOS_BASE_URL = "http://localhost:8000"

_EVIDENCIA_DE_EJEMPLO = {
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
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- validación de argumentos -----------------------------------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="case_id.*entero positivo"):
        await consultar_evidencia(0, 1)


@pytest.mark.asyncio
async def test_evidence_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="evidence_id.*entero positivo"):
        await consultar_evidencia(5, 0)
    with pytest.raises(ToolError, match="evidence_id.*entero positivo"):
        await consultar_evidencia(5, -3)


# --- respuesta válida del backend ------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_evidencia_encontrada_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(
        return_value=httpx.Response(200, json=_EVIDENCIA_DE_EJEMPLO)
    )

    resultado = await consultar_evidencia(5, 1)

    assert resultado == {"estado": "ok", "datos": _EVIDENCIA_DE_EJEMPLO}


# --- caso inexistente vs evidencia inexistente (mismo 404, detalle distinto) -


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_se_distingue_de_evidencia_inexistente():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/999/evidences/1").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await consultar_evidencia(999, 1)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso no encontrado"}


@pytest.mark.asyncio
@respx.mock
async def test_evidencia_inexistente_en_caso_real():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/999").mock(
        return_value=httpx.Response(404, json={"detail": "Evidencia no encontrada"})
    )

    resultado = await consultar_evidencia(5, 999)

    assert resultado == {"estado": "no_encontrado", "detalle": "Evidencia no encontrada"}


@pytest.mark.asyncio
@respx.mock
async def test_404_sin_cuerpo_json_usa_mensaje_de_respaldo():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/999").mock(
        return_value=httpx.Response(404, content=b"not json")
    )

    resultado = await consultar_evidencia(5, 999)

    assert resultado["estado"] == "no_encontrado"
    assert "999" in resultado["detalle"] and "5" in resultado["detalle"]


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
    peticion = respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_EVIDENCIA_DE_EJEMPLO),
        ]
    )

    resultado = await consultar_evidencia(5, 1)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await consultar_evidencia(5, 1)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(
        return_value=httpx.Response(422, json={"detail": "id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await consultar_evidencia(5, 1)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(return_value=httpx.Response(502))

    with pytest.raises(ToolError, match="error del servidor"):
        await consultar_evidencia(5, 1)


# --- error de conexión/timeout ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await consultar_evidencia(5, 1)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await consultar_evidencia(5, 1)


# -----------------------------------------------------------------------------
# Prueba real contra Casos local (SIN mocks). Se salta si no hay credenciales
# en el entorno o Casos no responde. Nunca crea/modifica/borra nada.
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

    # Se necesita un case_id/evidence_id reales. Se buscan dinámicamente
    # entre varios casos ya existentes en vez de asumir uno fijo — así el
    # test no depende de qué caso concreto tenga evidencias en esta base.
    from app.main import listar_evidencias_de_caso

    case_id = None
    evidence_id = None
    for candidato in (1, 8, 18, 19, 20):
        try:
            lista = await listar_evidencias_de_caso(candidato)
        except ToolError as exc:
            pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")
        if lista["estado"] == "ok":
            case_id = candidato
            evidence_id = lista["datos"]["evidencias"][0]["id"]
            break

    if case_id is None:
        pytest.skip("Ninguno de los casos de prueba conocidos tiene evidencias reales con las que probar.")

    resultado = await consultar_evidencia(case_id, evidence_id)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["id"] == evidence_id
