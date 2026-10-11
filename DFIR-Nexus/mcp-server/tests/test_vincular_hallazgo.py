"""
Tests de la tool `vincular_hallazgo` (Fase 2G, OSINT + Casos).

`PATCH /osint-cases/{case_type}/{id}/vinculacion`
(scam-shield/app/modules/osint/case_link/routes.py) es el endpoint REST
real, pero identifica la investigación por `case_type` + su id en la
tabla de origen (p. ej. `ip_cases.id`) — NO por `osint_findings.id`, que
es lo que esta tool recibe como `finding_id` (mismo identificador que
`consultar_hallazgo_osint`). Por eso la tool resuelve primero `case_type`/
`source_id` con `GET /osint-findings/{finding_id}` (mismo endpoint que ya
usa `consultar_hallazgo_osint`) y solo entonces llama al PATCH real — dos
peticiones HTTP reales por invocación con confirmado=True, ninguna con
confirmado=False.

Errores reales verificados en el código
(scam-shield/app/modules/osint/case_link/service.py):
- 404 en el GET: el hallazgo no existe.
- 404 en el PATCH: puede ser `InvestigationNotFoundError` (carrera
  improbable) o `TargetCaseNotFoundError` ("No existe el caso {id}, o
  está eliminado") — mismo código HTTP, `detail` distinto; esta tool no
  intenta adivinar cuál fue, propaga el mensaje real.
- Si `case_id` ya era el mismo, el backend no persiste nada y devuelve
  `cambiado=False` con HTTP 200 — no es un error, es un resultado válido.

Esta tool NO admite desvincular (case_id=None): scope explícito de la
Fase 2G ("Solo vincula, no desvincula" — ver enunciado y README).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import vincular_hallazgo

OSINT_BASE_URL = "http://localhost:8124"
CASOS_BASE_URL = "http://localhost:8000"

_HALLAZGO = {
    "id": 4,
    "case_type": "ip",
    "source_table": "ip_cases",
    "source_id": 4,
    "case_id": None,
    "subject_type": "ip_address",
    "subject_value": "203.0.113.45",
    "risk_score": 82,
    "risk_level": "high",
    "headline": "IP marcada en listas negras",
    "flag_count": 3,
    "analyzed_at": "2026-09-03T09:22:01",
    "created_at": "2026-09-03T09:22:01",
    "top_flags": ["blacklist_abuseipdb"],
    "details": {"country": "RU"},
}

_VINCULACION_OK = {
    "case_type": "ip",
    "id": 4,
    "case_id": 8,
    "cambiado": True,
    "auditoria_registrada": True,
    "auditoria_error": None,
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


def _mockear_hallazgo_ok(hallazgo: dict = _HALLAZGO) -> respx.Route:
    return respx.get(f"{OSINT_BASE_URL}/osint-findings/{hallazgo['id']}").mock(
        return_value=httpx.Response(200, json=hallazgo)
    )


# --- confirmado=False no realiza NINGUNA petición HTTP -----------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_false_no_hace_ninguna_peticion_http():
    # Ni siquiera la resolución case_type/source_id (el GET previo) debe
    # ocurrir: cero mocks registrados, cualquier llamada de red real
    # haría fallar el test por sí sola.
    with pytest.raises(ToolError, match="confirmado=true"):
        await vincular_hallazgo(4, 8, confirmado=False)


@pytest.mark.asyncio
async def test_finding_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="finding_id"):
        await vincular_hallazgo(0, 8, confirmado=True)
    with pytest.raises(ToolError, match="finding_id"):
        await vincular_hallazgo(-1, 8, confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="case_id"):
        await vincular_hallazgo(4, 0, confirmado=True)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_vincula_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    ruta_patch = respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        return_value=httpx.Response(200, json=_VINCULACION_OK)
    )

    resultado = await vincular_hallazgo(4, 8, confirmado=True)

    assert resultado == {"estado": "ok", "datos": _VINCULACION_OK}
    import json as _json

    assert _json.loads(ruta_patch.calls.last.request.content) == {"case_id": 8}


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_ya_vinculado_al_mismo_caso_no_es_error():
    _mockear_login_ok()
    _mockear_hallazgo_ok({**_HALLAZGO, "case_id": 8})
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        return_value=httpx.Response(
            200, json={"case_type": "ip", "id": 4, "case_id": 8, "cambiado": False}
        )
    )

    resultado = await vincular_hallazgo(4, 8, confirmado=True)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["cambiado"] is False


# --- no encontrado (hallazgo) --------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_hallazgo_inexistente_es_no_encontrado_sin_llegar_al_patch():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/999").mock(
        return_value=httpx.Response(404, json={"detail": "No existe el finding 999"})
    )
    # Deliberadamente SIN mockear el PATCH: si la tool lo intentara pese a
    # que el hallazgo no existe, respx haría fallar el test.

    resultado = await vincular_hallazgo(999, 8, confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe el finding 999"}


# --- no encontrado (caso destino) ------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_destino_inexistente_es_no_encontrado():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        return_value=httpx.Response(404, json={"detail": "No existe el caso 999, o está eliminado"})
    )

    resultado = await vincular_hallazgo(4, 999, confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe el caso 999, o está eliminado"}


# --- 401 + reautenticación (en el PATCH, el paso mutable) ------------------


@pytest.mark.asyncio
@respx.mock
async def test_401_en_el_patch_reautentica_una_vez_y_repite_la_peticion():
    login = respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "token-viejo", "token_type": "bearer", "expires_in": 7200}),
            httpx.Response(200, json={"access_token": "token-nuevo", "token_type": "bearer", "expires_in": 7200}),
        ]
    )
    _mockear_hallazgo_ok()
    peticion = respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_VINCULACION_OK),
        ]
    )

    resultado = await vincular_hallazgo(4, 8, confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 (en el PATCH) ------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_en_el_patch_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await vincular_hallazgo(4, 8, confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_en_el_patch_se_propaga_como_error_claro():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await vincular_hallazgo(4, 8, confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_en_el_patch_se_propaga_como_error_claro():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await vincular_hallazgo(4, 8, confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await vincular_hallazgo(4, 8, confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_en_el_get_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{OSINT_BASE_URL}/osint-findings/4").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await vincular_hallazgo(4, 8, confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_en_el_patch_se_propaga_como_error_claro():
    _mockear_login_ok()
    _mockear_hallazgo_ok()
    respx.patch(f"{OSINT_BASE_URL}/osint-cases/ip/4/vinculacion").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await vincular_hallazgo(4, 8, confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra OSINT + Casos locales (SIN mocks). Usa ÚNICAMENTE un
# hallazgo OSINT ya existente (nunca fabricado) y crea su PROPIO caso de
# prueba (vía crear_caso) como destino de la vinculación — así el efecto
# real y persistente de esta prueba queda acotado, como mínimo, a ese caso
# de prueba, nunca a un caso ya en uso.
#
# Si el hallazgo real elegido YA estaba vinculado a otro caso real antes de
# la prueba, ese vínculo original se restaura al final con una segunda
# llamada real a vincular_hallazgo (preferido: deja el sistema exactamente
# como estaba). Si NINGÚN hallazgo real está ya vinculado a un caso (esta
# tool no admite desvincular, así que solo se puede restaurar un estado
# "vinculado", nunca "sin vincular"), la prueba usa el primer hallazgo real
# de la lista de todos modos y NO intenta restaurarlo: la instrucción de
# esta fase pide explícitamente ejecutar una vinculación real y comprobar
# el resultado, no simularla. Ese efecto permanente e irreversible por esta
# vía queda documentado en el print final y en el informe de cierre.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_osint_y_casos_locales_si_esta_disponible():
    import os
    from datetime import datetime, timezone

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    from app.main import crear_caso, listar_hallazgos_osint

    try:
        listado = await listar_hallazgos_osint(limit=50)
    except ToolError as exc:
        pytest.skip(f"OSINT no disponible en {OSINT_BASE_URL}, o credenciales rechazadas: {exc}")

    if listado["estado"] != "ok" or not listado["datos"]["hallazgos"]:
        pytest.skip("No hay ningún hallazgo OSINT real con el que probar vincular_hallazgo.")

    hallazgos = listado["datos"]["hallazgos"]
    candidato = next((h for h in hallazgos if h["case_id"] is not None), None)
    restaurable = candidato is not None
    if candidato is None:
        candidato = hallazgos[0]

    finding_id = candidato["id"]
    case_id_original = candidato["case_id"]

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre = f"MCP-TEST-Fase2G-vincular_hallazgo-{marca}"
    try:
        caso_prueba = await crear_caso(nombre, "MCP Server (test automático)", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert caso_prueba["estado"] == "ok"
    case_id_prueba = caso_prueba["datos"]["id"]

    vinculado = await vincular_hallazgo(finding_id, case_id_prueba, confirmado=True)
    assert vinculado["estado"] == "ok"
    assert vinculado["datos"]["cambiado"] is True
    assert vinculado["datos"]["case_id"] == case_id_prueba

    if restaurable:
        restaurado = await vincular_hallazgo(finding_id, case_id_original, confirmado=True)
        assert restaurado["estado"] == "ok"
        assert restaurado["datos"]["cambiado"] is True
        assert restaurado["datos"]["case_id"] == case_id_original
        print(
            f"\n[test_real_contra_osint_y_casos_locales_si_esta_disponible] "
            f"finding_id={finding_id} vinculado temporalmente a case_id={case_id_prueba} "
            f"(caso de prueba {nombre!r}) y restaurado a su case_id original={case_id_original}. "
            f"El caso de prueba id={case_id_prueba} queda en el sistema, documentado aquí."
        )
    else:
        print(
            f"\n[test_real_contra_osint_y_casos_locales_si_esta_disponible] AVISO: "
            f"finding_id={finding_id} no tenía ningún caso vinculado antes de esta prueba "
            f"(case_id original=None) y esta tool no admite desvincular, así que NO se ha "
            f"restaurado: queda vinculado de forma permanente a case_id={case_id_prueba} "
            f"(caso de prueba {nombre!r}). Documentado aquí para poder revertirlo manualmente "
            f"(UPDATE directo, o desde el frontend) si se desea."
        )
