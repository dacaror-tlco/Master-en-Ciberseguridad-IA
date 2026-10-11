"""
Tests de la tool `verificar_integridad_evidencia` (Fase 2B).

El contrato viene de `EvidenceIntegrityCheck`
(backend/app/modules/cases/schemas.py): evidence_id, algoritmo,
hash_registrado, hash_actual, integro. Se recalcula sha256(valor) en el
propio backend y se compara con el hash guardado al crear la evidencia —
esta tool solo lee y reenvía esa comparación, no calcula nada por su
cuenta.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import verificar_integridad_evidencia

CASOS_BASE_URL = "http://localhost:8000"


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
        await verificar_integridad_evidencia(0, 1)


@pytest.mark.asyncio
async def test_evidence_id_no_positivo_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="evidence_id.*entero positivo"):
        await verificar_integridad_evidencia(5, 0)


# --- comportamiento específico de integridad --------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_evidencia_integra_devuelve_integro_true():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        return_value=httpx.Response(
            200,
            json={
                "evidence_id": 1,
                "algoritmo": "sha256",
                "hash_registrado": "a" * 64,
                "hash_actual": "a" * 64,
                "integro": True,
            },
        )
    )

    resultado = await verificar_integridad_evidencia(5, 1)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["integro"] is True
    assert resultado["datos"]["hash_registrado"] == resultado["datos"]["hash_actual"]


@pytest.mark.asyncio
@respx.mock
async def test_evidencia_no_integra_devuelve_integro_false_sin_ocultarlo():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        return_value=httpx.Response(
            200,
            json={
                "evidence_id": 1,
                "algoritmo": "sha256",
                "hash_registrado": "a" * 64,
                "hash_actual": "f" * 64,
                "integro": False,
            },
        )
    )

    resultado = await verificar_integridad_evidencia(5, 1)

    # La tool no debe "arreglar" ni esconder una integridad rota: la
    # reporta tal cual la da el backend.
    assert resultado["estado"] == "ok"
    assert resultado["datos"]["integro"] is False
    assert resultado["datos"]["hash_registrado"] != resultado["datos"]["hash_actual"]


# --- caso/evidencia inexistente ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/999/evidences/1/integridad").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await verificar_integridad_evidencia(999, 1)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso no encontrado"}


@pytest.mark.asyncio
@respx.mock
async def test_evidencia_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/999/integridad").mock(
        return_value=httpx.Response(404, json={"detail": "Evidencia no encontrada"})
    )

    resultado = await verificar_integridad_evidencia(5, 999)

    assert resultado == {"estado": "no_encontrado", "detalle": "Evidencia no encontrada"}


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
    peticion = respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(
                200,
                json={
                    "evidence_id": 1,
                    "algoritmo": "sha256",
                    "hash_registrado": "a" * 64,
                    "hash_actual": "a" * 64,
                    "integro": True,
                },
            ),
        ]
    )

    resultado = await verificar_integridad_evidencia(5, 1)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await verificar_integridad_evidencia(5, 1)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        return_value=httpx.Response(422, json={"detail": "id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await verificar_integridad_evidencia(5, 1)


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await verificar_integridad_evidencia(5, 1)


# --- error de conexión/timeout ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await verificar_integridad_evidencia(5, 1)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases/5/evidences/1/integridad").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await verificar_integridad_evidencia(5, 1)


# -----------------------------------------------------------------------------
# Prueba real contra Casos local (SIN mocks). Se salta si no hay credenciales
# en el entorno, si Casos no responde, o si el caso #1 no tiene evidencias
# reales con las que probar. Nunca crea/modifica/borra nada.
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

    resultado = await verificar_integridad_evidencia(case_id, evidence_id)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["evidence_id"] == evidence_id
    assert isinstance(resultado["datos"]["integro"], bool)
