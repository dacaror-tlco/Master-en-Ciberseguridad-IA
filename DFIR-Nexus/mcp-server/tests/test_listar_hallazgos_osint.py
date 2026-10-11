"""
Tests de la tool `listar_hallazgos_osint` (Fase 2E, OSINT).

`GET /osint-findings` (scam-shield/app/modules/osint/findings/routes.py)
es la vista de lectura consolidada de los 8 tipos de análisis OSINT
(dominio, email, wallet, typosquatting, teléfono, CNMV, IP, imagen). No
comprueba existencia de `case_id` — es un filtro más, no una referencia
obligatoria — así que nunca puede distinguir "no hay hallazgos para ese
caso" de "ese caso no existe": solo "ok"/"sin_resultados", igual que
Timeline/Informes en la Fase 2C.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import listar_hallazgos_osint

OSINT_BASE_URL = "http://localhost:8124"
CASOS_BASE_URL = "http://localhost:8000"

_HALLAZGOS_DE_EJEMPLO = [
    {
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
    },
    {
        "id": 37,
        "case_type": "domain",
        "source_table": "domain_analysis_cases",
        "source_id": 37,
        "case_id": 8,
        "subject_type": "domain",
        "subject_value": "evolve.es",
        "risk_score": 5,
        "risk_level": "low",
        "headline": "Dominio evolve.es — RIESGO BAJO (5)",
        "flag_count": 0,
        "analyzed_at": "2026-09-21T10:15:48",
        "created_at": "2026-09-21T10:15:48",
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
async def test_skip_negativo_se_rechaza():
    with pytest.raises(ToolError, match="skip"):
        await listar_hallazgos_osint(skip=-1)


@pytest.mark.asyncio
async def test_limit_fuera_de_rango_se_rechaza():
    with pytest.raises(ToolError, match="limit"):
        await listar_hallazgos_osint(limit=0)
    with pytest.raises(ToolError, match="limit"):
        await listar_hallazgos_osint(limit=201)


@pytest.mark.asyncio
async def test_min_risk_score_fuera_de_rango_se_rechaza():
    with pytest.raises(ToolError, match="min_risk_score"):
        await listar_hallazgos_osint(min_risk_score=-1)
    with pytest.raises(ToolError, match="min_risk_score"):
        await listar_hallazgos_osint(min_risk_score=101)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza():
    with pytest.raises(ToolError, match="case_id"):
        await listar_hallazgos_osint(case_id=0)


# --- respuesta correcta / filtros -------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_sin_filtros_devuelve_todos():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(
        return_value=httpx.Response(200, json=_HALLAZGOS_DE_EJEMPLO)
    )

    resultado = await listar_hallazgos_osint()

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 2
    assert resultado["datos"]["hallazgos"] == _HALLAZGOS_DE_EJEMPLO
    assert resultado["datos"]["skip"] == 0
    assert resultado["datos"]["limit"] == 50


@pytest.mark.asyncio
@respx.mock
async def test_filtros_indicados_se_envian_y_los_no_indicados_se_omiten():
    _mockear_login_ok()
    ruta = respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(
        return_value=httpx.Response(200, json=[_HALLAZGOS_DE_EJEMPLO[0]])
    )

    resultado = await listar_hallazgos_osint(case_id=8, risk_level="high", min_risk_score=50)

    peticion = ruta.calls.last.request
    assert peticion.url.params["case_id"] == "8"
    assert peticion.url.params["risk_level"] == "high"
    assert peticion.url.params["min_risk_score"] == "50"
    assert "case_type" not in peticion.url.params
    assert "subject_value" not in peticion.url.params
    assert resultado["estado"] == "ok"


# --- lista vacía (sin_resultados) ------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_sin_coincidencias_es_sin_resultados():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(return_value=httpx.Response(200, json=[]))

    resultado = await listar_hallazgos_osint(case_id=999)

    assert resultado["estado"] == "sin_resultados"
    assert "detalle" in resultado


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
    peticion = respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_HALLAZGOS_DE_EJEMPLO),
        ]
    )

    resultado = await listar_hallazgos_osint()

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await listar_hallazgos_osint()


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(
        return_value=httpx.Response(422, json={"detail": "parámetros inválidos"})
    )

    with pytest.raises(ToolError, match="422"):
        await listar_hallazgos_osint()


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await listar_hallazgos_osint()


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await listar_hallazgos_osint()


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await listar_hallazgos_osint()


# -----------------------------------------------------------------------------
# Prueba real contra OSINT local (SIN mocks). Se salta si no hay credenciales,
# o si OSINT no responde. Nunca crea/modifica/vincula nada.
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

    try:
        resultado = await listar_hallazgos_osint(limit=5)
    except ToolError as exc:
        pytest.skip(f"OSINT no disponible en {OSINT_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] in ("ok", "sin_resultados")
