"""
Tests de la tool `guardar_eventos_tracking` (Fase 2H, Tracking).

`POST /cases/{case_id}/tracking/events` (track-inc/app/modules/tracking/
routes.py) verificado en el código real: persiste eventos YA
clasificados (`SaveEventsRequest.eventos: list[AnalyzePreviewItem]`) —
distinto de `/analyze`, que sube y clasifica un log crudo (fuera de esta
fase, ver enunciado: "No implementar análisis de logs/OSINT todavía").

Estructura mínima real de cada evento (`AnalyzePreviewItem`): `hora`
(datetime), `evento` (str, no vacío), `severidad` (baja|media|alta|
critica); `usuario_detectado` opcional, máximo 100 caracteres (mismo
límite que la columna `tracking_events.usuario_detectado`). Esta tool
valida todo eso, y el volumen del array (máximo
`_MAX_EVENTOS_TRACKING_POR_LLAMADA`, un límite propio de la tool — el
backend no impone ninguno), ANTES de tocar la red.

Errores reales verificados en `service.py`:
- 404: `CaseNotFoundError` — el caso no existe.
- 409: `CasoNoModificableError` (caso eliminado o archivado) o
  `LogYaGuardadoError` (mismo `sha256_log` ya guardado en el caso, sin
  `forzar=True`) — mismo HTTP, `detail` distinto.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import guardar_eventos_tracking

TRACKING_BASE_URL = "http://localhost:8001"
CASOS_BASE_URL = "http://localhost:8000"

_EVENTO_VALIDO = {"hora": "2026-09-01T10:00:00", "evento": "Login fallido", "severidad": "media"}

_RESPUESTA_GUARDADO = {
    "guardados": 1,
    "tracking_events": [
        {
            "id": 501,
            "case_id": 8,
            "hora": "2026-09-01T10:00:00",
            "evento": "Login fallido",
            "severidad": "media",
            "fuente_log": "auth.log",
            "usuario_detectado": None,
            "regla": None,
            "hora_inferida": None,
        }
    ],
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
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="entero positivo"):
        await guardar_eventos_tracking(0, "auth.log", [_EVENTO_VALIDO], confirmado=True)


@pytest.mark.asyncio
async def test_fuente_log_vacia_o_demasiado_larga_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="fuente_log"):
        await guardar_eventos_tracking(8, "   ", [_EVENTO_VALIDO], confirmado=True)
    with pytest.raises(ToolError, match="fuente_log"):
        await guardar_eventos_tracking(8, "x" * 101, [_EVENTO_VALIDO], confirmado=True)


@pytest.mark.asyncio
async def test_eventos_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="vacío"):
        await guardar_eventos_tracking(8, "auth.log", [], confirmado=True)


@pytest.mark.asyncio
async def test_demasiados_eventos_se_rechaza_antes_que_confirmado():
    eventos = [_EVENTO_VALIDO] * 501
    with pytest.raises(ToolError, match="500"):
        await guardar_eventos_tracking(8, "auth.log", eventos, confirmado=True)


@pytest.mark.asyncio
async def test_sha256_log_invalido_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="SHA-256"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True, sha256_log="no-es-un-hash")


@pytest.mark.asyncio
async def test_evento_no_es_objeto_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match=r"eventos\[0\]"):
        await guardar_eventos_tracking(8, "auth.log", ["no soy un objeto"], confirmado=True)


@pytest.mark.asyncio
async def test_evento_sin_hora_se_rechaza_antes_que_confirmado():
    malo = {"evento": "algo", "severidad": "baja"}
    with pytest.raises(ToolError, match="'hora'"):
        await guardar_eventos_tracking(8, "auth.log", [malo], confirmado=True)


@pytest.mark.asyncio
async def test_evento_sin_texto_de_evento_se_rechaza_antes_que_confirmado():
    malo = {"hora": "2026-09-01T10:00:00", "evento": "   ", "severidad": "baja"}
    with pytest.raises(ToolError, match="'evento'"):
        await guardar_eventos_tracking(8, "auth.log", [malo], confirmado=True)


@pytest.mark.asyncio
async def test_evento_con_severidad_invalida_se_rechaza_antes_que_confirmado():
    malo = {"hora": "2026-09-01T10:00:00", "evento": "algo", "severidad": "grave"}
    with pytest.raises(ToolError, match="severidad"):
        await guardar_eventos_tracking(8, "auth.log", [malo], confirmado=True)


@pytest.mark.asyncio
async def test_evento_con_usuario_detectado_demasiado_largo_se_rechaza_antes_que_confirmado():
    malo = {**_EVENTO_VALIDO, "usuario_detectado": "x" * 101}
    with pytest.raises(ToolError, match="usuario_detectado"):
        await guardar_eventos_tracking(8, "auth.log", [malo], confirmado=True)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_guarda_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    ruta = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(200, json=_RESPUESTA_GUARDADO)
    )

    resultado = await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)

    assert resultado == {"estado": "ok", "datos": _RESPUESTA_GUARDADO}
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {
        "case_id": 8,
        "fuente_log": "auth.log",
        "eventos": [_EVENTO_VALIDO],
        "sha256_log": None,
        "forzar": False,
    }


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_con_sha256_log_y_forzar_los_envia_tal_cual():
    _mockear_login_ok()
    hash_log = "a" * 64
    ruta = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(200, json=_RESPUESTA_GUARDADO)
    )

    resultado = await guardar_eventos_tracking(
        8, "auth.log", [_EVENTO_VALIDO], confirmado=True, sha256_log=hash_log, forzar=True
    )

    assert resultado["estado"] == "ok"
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo["sha256_log"] == hash_log
    assert cuerpo["forzar"] is True


# --- no encontrado -----------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/999/tracking/events").mock(
        return_value=httpx.Response(404, json={"detail": "No existe ningún caso con id=999"})
    )

    resultado = await guardar_eventos_tracking(999, "auth.log", [_EVENTO_VALIDO], confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe ningún caso con id=999"}


# --- conflicto (409, dos causas posibles) -----------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_no_modificable_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(409, json={"detail": "El caso está archivado: es un registro histórico inmutable"})
    )

    resultado = await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)

    assert resultado["estado"] == "conflicto"
    assert "archivado" in resultado["detalle"]


@pytest.mark.asyncio
@respx.mock
async def test_log_ya_guardado_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(
            409, json={"detail": "Este fichero de log ya se guardó en el caso (3 eventos)."}
        )
    )

    resultado = await guardar_eventos_tracking(
        8, "auth.log", [_EVENTO_VALIDO], confirmado=True, sha256_log="a" * 64
    )

    assert resultado["estado"] == "conflicto"
    assert "ya se guardó" in resultado["detalle"]


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
    peticion = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_RESPUESTA_GUARDADO),
        ]
    )

    resultado = await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(
        return_value=httpx.Response(422, json={"detail": "evento inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/events").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await guardar_eventos_tracking(8, "auth.log", [_EVENTO_VALIDO], confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Tracking local (SIN mocks). Crea su PROPIO caso de
# prueba (vía crear_caso, Fase 2G) y guarda en él un conjunto pequeño (2) de
# eventos de tracking reales, comprobando después con listar_eventos_tracking
# (Fase 2D) que aparecen de verdad.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_tracking_local_si_esta_disponible():
    import os
    from datetime import datetime, timezone

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    from app.main import crear_caso, listar_eventos_tracking

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre_caso = f"MCP-TEST-Fase2H-guardar_eventos_tracking-{marca}"

    try:
        caso = await crear_caso(nombre_caso, "MCP Server (test automático)", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert caso["estado"] == "ok"
    case_id = caso["datos"]["id"]

    eventos = [
        {"hora": "2026-09-01T10:00:00", "evento": "Login fallido de prueba MCP", "severidad": "media"},
        {"hora": "2026-09-01T10:05:00", "evento": "Escalada de privilegios de prueba MCP", "severidad": "alta"},
    ]

    try:
        guardado = await guardar_eventos_tracking(
            case_id, f"mcp-test-{marca}.log", eventos, confirmado=True
        )
    except ToolError as exc:
        pytest.skip(f"Tracking no disponible en {TRACKING_BASE_URL}, o credenciales rechazadas: {exc}")

    assert guardado["estado"] == "ok"
    assert guardado["datos"]["guardados"] == 2

    listado = await listar_eventos_tracking(case_id)
    assert listado["estado"] == "ok"
    assert listado["datos"]["total"] == 2

    print(
        f"\n[test_real_contra_tracking_local_si_esta_disponible] Caso de prueba id={case_id} "
        f"nombre={nombre_caso!r}, 2 eventos de tracking guardados y verificados."
    )
