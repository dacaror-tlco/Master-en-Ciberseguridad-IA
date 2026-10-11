"""
Tests de la tool `recalcular_cronologia` (Fase 2F) — la primera tool de
escritura del MCP Server.

`POST /timeline/cases/{case_id}/refresh` (timeline/app/modules/timeline/
routes.py) verificado en el código real:
- Nunca devuelve 404: no comprueba si el caso existe, solo reconstruye
  `timeline_events` desde las tres fuentes (vacío si no hay nada que
  correlacionar). Por eso NO hay test de "caso inexistente" en el sentido
  de un 404 real — sería fabricar un comportamiento que el backend no
  tiene.
- El único error real posible es un 500 genérico (el handler envuelve
  cualquier excepción con un mensaje sanitizado, sin detalle de BD —
  auditoría H-04 del propio backend).
- El borrado + inserción es atómico en el propio backend
  (`db.rollback()` ante cualquier fallo, ver `service.py`): esta tool no
  necesita — ni podría — añadir ninguna garantía transaccional propia,
  solo reenviar la petición.

Los tests de 404/422 de esta suite (pedidos como mínimo por el
enunciado) ejercitan el camino de error GENÉRICO de `_peticion_segura`
(el mismo que ya usan las demás tools), no un comportamiento real y
documentado de este endpoint concreto — así se indica en cada uno.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import recalcular_cronologia

TIMELINE_BASE_URL = "http://localhost:8002"
CASOS_BASE_URL = "http://localhost:8000"

_EVENTOS_RECALCULADOS = [
    {
        "id": 448,
        "case_id": 8,
        "fecha_hora": "2026-09-02T20:22:36",
        "descripcion": "imagen_disco: EV-001 ...",
        "origen_modulo": "evidence",
        "origen_id": 4,
        "orden": 1,
    },
    {
        "id": 451,
        "case_id": 8,
        "fecha_hora": "2026-09-03T00:21:57",
        "descripcion": "Detección de escaneo de puertos",
        "origen_modulo": "tracking",
        "origen_id": 22,
        "orden": 2,
    },
]


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
    # Ni siquiera se registra ningún mock de red: si la tool intentara
    # llamar a cualquier URL no interceptada, respx haría fallar el test
    # (comportamiento por defecto de @respx.mock: solo permite lo mockeado).
    # No mockear nada es, aquí, la propia aserción de "no hizo ninguna
    # petición".
    with pytest.raises(ToolError, match="confirmado=true"):
        await recalcular_cronologia(8, confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    # Se comprueba primero case_id, independientemente de confirmado — ni
    # siquiera con confirmado=True se llega a intentar nada con un id
    # inválido.
    with pytest.raises(ToolError, match="entero positivo"):
        await recalcular_cronologia(0, confirmado=True)
    with pytest.raises(ToolError, match="entero positivo"):
        await recalcular_cronologia(-1, confirmado=False)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_recalcula_y_devuelve_los_eventos_reales():
    _mockear_login_ok()
    ruta = respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        return_value=httpx.Response(200, json=_EVENTOS_RECALCULADOS)
    )

    resultado = await recalcular_cronologia(8, confirmado=True)

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 2
    assert resultado["datos"]["eventos"] == _EVENTOS_RECALCULADOS
    assert ruta.calls.last.request.method == "POST"


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_sin_fuentes_devuelve_lista_vacia_no_error():
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(return_value=httpx.Response(200, json=[]))

    resultado = await recalcular_cronologia(8, confirmado=True)

    assert resultado == {"estado": "ok", "datos": {"total": 0, "eventos": []}}


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
    peticion = respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_EVENTOS_RECALCULADOS),
        ]
    )

    resultado = await recalcular_cronologia(8, confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await recalcular_cronologia(8, confirmado=True)


# --- 404 (camino genérico: este endpoint real no lo produce) --------------


@pytest.mark.asyncio
@respx.mock
async def test_404_hipotetico_se_propaga_por_el_camino_generico():
    """El backend real de Timeline nunca devuelve 404 en este endpoint
    (verificado en el código: no comprueba existencia del caso). Este
    test cubre el requisito mínimo del enunciado ejercitando el fallback
    genérico de `_peticion_segura` para cualquier status no reconocido
    explícitamente — no afirma que el 404 sea un comportamiento real de
    Timeline."""
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        return_value=httpx.Response(404, json={"detail": "hipotético, no real en este endpoint"})
    )

    with pytest.raises(ToolError, match="404"):
        await recalcular_cronologia(8, confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        return_value=httpx.Response(422, json={"detail": "case_id inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await recalcular_cronologia(8, confirmado=True)


# --- 5xx (real: el único error documentado de este endpoint) --------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        return_value=httpx.Response(500, json={"detail": "Error al recalcular la línea temporal"})
    )

    with pytest.raises(ToolError, match="error del servidor"):
        await recalcular_cronologia(8, confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await recalcular_cronologia(8, confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TIMELINE_BASE_URL}/timeline/cases/8/refresh").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await recalcular_cronologia(8, confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Timeline local (SIN mocks). SOLO con confirmado=True
# aquí, exactamente como pide el enunciado. Recalcula de verdad la
# cronología del caso #8 (mismo caso ya usado en la Fase 2C) y comprueba que
# el resultado sigue siendo coherente: cada evento resuelto trae case_id,
# fecha_hora, origen_modulo/origen_id y un "orden" secuencial sin huecos ni
# duplicados. No crea ni borra casos ni evidencias — recalcular_cronologia
# no toca esas tablas, solo relee de ellas.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_timeline_local_si_esta_disponible():
    import os

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    try:
        resultado = await recalcular_cronologia(8, confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Timeline no disponible en {TIMELINE_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    eventos = resultado["datos"]["eventos"]

    # Coherencia del resultado: "orden" es una secuencia 1..N sin huecos, y
    # cada evento trae los campos reales del contrato de Timeline.
    ordenes = [e["orden"] for e in eventos]
    assert ordenes == list(range(1, len(eventos) + 1))
    for evento in eventos:
        assert evento["case_id"] == 8
        assert evento["origen_modulo"] in ("evidence", "tracking", "osint")
        assert evento["origen_id"] > 0
