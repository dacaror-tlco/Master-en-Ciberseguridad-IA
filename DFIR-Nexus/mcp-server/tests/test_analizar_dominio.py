"""
Tests de la tool `analizar_dominio` (Fase 2I, OSINT) — la única de las 8
tools de análisis OSINT que expone esta fase (la de menor riesgo:
`domain` como cadena, sin fichero, sin PII directa).

`POST /analysis/domain` (scam-shield/app/modules/osint/domain/routes.py)
verificado en el código real: a diferencia de las tools de lectura de
OSINT (Fase 2E), este endpoint SÍ PERSISTE — `service.run_domain_analysis`
llama a `repository.create_case` (nueva fila en `domain_cases`),
`integrity_service.record_evidence` y `findings_service.record_finding`
(nueva fila en `osint_findings`) — por eso esta tool exige
`confirmado=true`, a diferencia de `analizar_log` (Fase 2I, Tracking, que
NO persiste nada).

Verificado también: `normalize_domain` nunca lanza (no hay validación de
formato de dominio en el backend: cualquier cadena "vale", las fuentes
externas que fallan simplemente se anotan en `errors` sin tumbar la
petición) y `repository.create_case` no comprueba que `case_id` exista —
por eso no hay ningún 404/409 real que fabricar aquí: los tests de esos
códigos ejercitan el camino genérico de `_peticion_segura`, no un
comportamiento documentado de este endpoint.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import analizar_dominio

OSINT_BASE_URL = "http://localhost:8124"
CASOS_BASE_URL = "http://localhost:8000"

_RESULTADO_ANALISIS = {
    "id": 55,
    "domain": "ejemplo-sospechoso.com",
    "analyzed_at": "2026-09-29T10:00:00",
    "created_at": "2026-09-29T10:00:00",
    "whois": None,
    "ssl": None,
    "virustotal": {"malicious_count": 0, "suspicious_count": 0, "harmless_count": 10, "undetected_count": 5, "reputation": 0, "categories": []},
    "resolved_ip": "203.0.113.10",
    "abuseipdb": None,
    "dns": None,
    "ip_reputations": [],
    "crtsh": None,
    "wayback": None,
    "risk_flags": [],
    "risk_score": 5,
    "errors": [],
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


# --- confirmado=False no realiza NINGUNA petición HTTP ----------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_false_no_hace_ninguna_peticion_http():
    with pytest.raises(ToolError, match="confirmado=true"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=False)


@pytest.mark.asyncio
async def test_domain_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="domain"):
        await analizar_dominio("   ", confirmado=True)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="entero positivo"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True, case_id=0)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_analiza_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    ruta = respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(
        return_value=httpx.Response(200, json=_RESULTADO_ANALISIS)
    )

    resultado = await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)

    assert resultado == {"estado": "ok", "datos": _RESULTADO_ANALISIS}
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {"domain": "ejemplo-sospechoso.com", "case_id": None}


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_con_case_id_lo_envia_tal_cual():
    _mockear_login_ok()
    ruta = respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(
        return_value=httpx.Response(200, json={**_RESULTADO_ANALISIS, "case_id": 8})
    )

    resultado = await analizar_dominio("ejemplo-sospechoso.com", confirmado=True, case_id=8)

    assert resultado["estado"] == "ok"
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {"domain": "ejemplo-sospechoso.com", "case_id": 8}


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
    peticion = respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_RESULTADO_ANALISIS),
        ]
    )

    resultado = await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(
        return_value=httpx.Response(422, json={"detail": "domain inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{OSINT_BASE_URL}/analysis/domain").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await analizar_dominio("ejemplo-sospechoso.com", confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra OSINT local (SIN mocks). ÚNICAMENTE con
# confirmado=True, como pide el enunciado. Usa "example.com" (dominio
# reservado para documentación por IANA/RFC 2606: no pertenece a nadie que
# pueda verse afectado) como dominio de laboratorio, y NO lo vincula a
# ningún caso (case_id=None) — persiste un hallazgo real en OSINT, con
# consumo real (aunque mínimo, una única llamada) de las cuotas de
# VirusTotal/AbuseIPDB configuradas en scam-shield.
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
        resultado = await analizar_dominio("example.com", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"OSINT no disponible en {OSINT_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    datos = resultado["datos"]
    assert datos["domain"] == "example.com"
    assert isinstance(datos["risk_score"], int)

    print(
        f"\n[test_real_contra_osint_local_si_esta_disponible] Hallazgo OSINT real creado: "
        f"id={datos['id']} domain=example.com risk_score={datos['risk_score']} "
        f"errors={datos['errors']!r} — consumo real (mínimo) de cuotas de fuentes externas."
    )
