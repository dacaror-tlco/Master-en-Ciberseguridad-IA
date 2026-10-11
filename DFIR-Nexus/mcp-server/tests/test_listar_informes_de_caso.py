"""
Tests de la tool `listar_informes_de_caso` (Fase 2C, Informes).

`GET /cases/{case_id}/reports` (sharingan/app/modules/reports/routes.py)
tampoco comprueba si el caso existe — igual que Timeline, nunca puede
devolver "no_encontrado" desde este endpoint (ver test_*.py de Timeline
para la misma limitación verificada en código real).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import listar_informes_de_caso

INFORMES_BASE_URL = "http://localhost:8003"
CASOS_BASE_URL = "http://localhost:8000"

_INFORMES_DE_EJEMPLO = [
    {
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
async def test_case_id_no_positivo_se_rechaza_sin_llamar_a_informes():
    with pytest.raises(ToolError, match="entero positivo"):
        await listar_informes_de_caso(0)


# --- caso con informes -------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_con_informes_devuelve_los_datos_reales():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(
        return_value=httpx.Response(200, json=_INFORMES_DE_EJEMPLO)
    )

    resultado = await listar_informes_de_caso(8)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 1
    assert resultado["datos"]["informes"] == _INFORMES_DE_EJEMPLO


# --- caso sin informes ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_sin_informes_es_sin_resultados():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(return_value=httpx.Response(200, json=[]))

    resultado = await listar_informes_de_caso(8)

    assert resultado["estado"] == "sin_resultados"
    assert "detalle" in resultado


# --- la petición va al backend correcto (Informes, no Casos) ---------------


@pytest.mark.asyncio
@respx.mock
async def test_la_peticion_de_datos_va_a_informes_no_a_casos():
    _mockear_login_ok()
    ruta = respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(return_value=httpx.Response(200, json=[]))

    await listar_informes_de_caso(8)

    assert ruta.called


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
    peticion = respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_INFORMES_DE_EJEMPLO),
        ]
    )

    resultado = await listar_informes_de_caso(8)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await listar_informes_de_caso(8)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await listar_informes_de_caso(8)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(return_value=httpx.Response(503))

    with pytest.raises(ToolError, match="error del servidor"):
        await listar_informes_de_caso(8)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await listar_informes_de_caso(8)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{INFORMES_BASE_URL}/cases/8/reports").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await listar_informes_de_caso(8)


# -----------------------------------------------------------------------------
# Prueba real contra Informes local (SIN mocks). Se salta si no hay
# credenciales en el entorno, si los backends no responden, o si ninguno de
# los casos de prueba conocidos tiene informes reales todavía.
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

    resultado = None
    for candidato in (1, 8, 18, 19, 20):
        try:
            intento = await listar_informes_de_caso(candidato)
        except ToolError as exc:
            pytest.skip(f"Informes no disponible en {INFORMES_BASE_URL}, o credenciales rechazadas: {exc}")
        if intento["estado"] == "ok":
            resultado = intento
            break

    if resultado is None:
        pytest.skip("Ninguno de los casos de prueba conocidos tiene informes reales con los que probar.")

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] > 0
