"""
Tests de la tool `verificar_integridad_tracking` (Fase 2D, Tracking).

Contrato de `GET /cases/{case_id}/tracking/verify`:
`VerifyIntegrityResponse {ok, mensaje, problemas[]}` — deliberadamente sin
hashes ni detalle criptográfico (track-inc/app/modules/tracking/
schemas.py lo documenta explícitamente). Esta tool reenvía el veredicto
tal cual, sin recalcular ni alterar nada.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import verificar_integridad_tracking

TRACKING_BASE_URL = "http://localhost:8001"
CASOS_BASE_URL = "http://localhost:8000"


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
        await verificar_integridad_tracking(0)


# --- integridad correcta ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_integridad_correcta_devuelve_ok_true_sin_alterar_nada():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(
        return_value=httpx.Response(200, json={"ok": True, "mensaje": "Cadena íntegra.", "problemas": []})
    )

    resultado = await verificar_integridad_tracking(8)

    assert resultado == {
        "estado": "ok",
        "datos": {"ok": True, "mensaje": "Cadena íntegra.", "problemas": []},
    }


# --- integridad incorrecta: se reenvía tal cual, sin ocultar ni "arreglar" -


@pytest.mark.asyncio
@respx.mock
async def test_integridad_incorrecta_se_reenvia_sin_ocultarla():
    _mockear_login_ok()
    respx_json = {
        "ok": False,
        "mensaje": "2 eventos no coinciden con la cadena registrada.",
        "problemas": ["evento id=23 modificado", "evento id=25 no encontrado en la cadena"],
    }
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(return_value=httpx.Response(200, json=respx_json))

    resultado = await verificar_integridad_tracking(8)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["ok"] is False
    assert resultado["datos"]["problemas"] == respx_json["problemas"]
    # Ninguna clave de hash/criptografía inventada por la tool: solo lo que
    # ya trae el backend (que deliberadamente no expone hashes).
    assert set(resultado["datos"].keys()) == {"ok", "mensaje", "problemas"}


# --- caso inexistente --------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/999/tracking/verify").mock(
        return_value=httpx.Response(404, json={"detail": "Caso 999 no encontrado"})
    )

    resultado = await verificar_integridad_tracking(999)

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
    peticion = respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json={"ok": True, "mensaje": "Cadena íntegra.", "problemas": []}),
        ]
    )

    resultado = await verificar_integridad_tracking(8)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await verificar_integridad_tracking(8)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await verificar_integridad_tracking(8)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await verificar_integridad_tracking(8)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await verificar_integridad_tracking(8)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{TRACKING_BASE_URL}/cases/8/tracking/verify").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await verificar_integridad_tracking(8)


# -----------------------------------------------------------------------------
# Prueba real contra Tracking local (SIN mocks). Se salta si no hay
# credenciales, o si Tracking no responde. Verify no requiere que haya
# eventos: un caso real sin eventos también da un veredicto válido (cadena
# vacía = íntegra), así que se prueba directamente contra el caso #8.
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

    try:
        resultado = await verificar_integridad_tracking(8)
    except ToolError as exc:
        pytest.skip(f"Tracking no disponible en {TRACKING_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] in ("ok", "no_encontrado")
    if resultado["estado"] == "ok":
        assert "ok" in resultado["datos"]
        assert "mensaje" in resultado["datos"]
