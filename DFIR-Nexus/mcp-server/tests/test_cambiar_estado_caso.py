"""
Tests de la tool `cambiar_estado_caso` (Fase 2G, Casos).

`PUT /cases/{case_id}` con únicamente `{"estado": ...}` en el cuerpo
(`CaseUpdate` tiene todos los campos opcionales y el servicio usa
`model_dump(exclude_unset=True)`, ver backend/app/modules/cases/
service.py::update_case) — por eso esta tool puede reutilizar el update
genérico como un cambio de estado puro, sin tocar nombre/responsable/
descripcion.

Errores reales verificados en el código (routes.py + state_machine.py):
- 404: caso no encontrado.
- 409 (tres causas distintas, mismo código HTTP, `detail` distinto):
  caso eliminado lógicamente, caso archivado (terminal, inmutable), o
  transición de estado no permitida (ver TRANSICIONES_VALIDAS). Esta tool
  no intenta adivinar cuál de las tres fue: propaga el `detail` real bajo
  `estado="conflicto"`.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import cambiar_estado_caso

CASOS_BASE_URL = "http://localhost:8000"

_CASO_ACTUALIZADO = {
    "id": 8,
    "nombre": "Caso existente",
    "descripcion": None,
    "responsable": "Yolanda",
    "estado": "en_progreso",
    "fecha_creacion": "2026-09-01T10:00:00",
    "fecha_actualizacion": "2026-09-29T10:00:00",
    "eliminado": False,
    "fecha_eliminacion": None,
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
        await cambiar_estado_caso(8, "en_progreso", confirmado=False)


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="entero positivo"):
        await cambiar_estado_caso(0, "en_progreso", confirmado=True)
    with pytest.raises(ToolError, match="entero positivo"):
        await cambiar_estado_caso(-1, "en_progreso", confirmado=False)


@pytest.mark.asyncio
async def test_nuevo_estado_invalido_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="abierto"):
        await cambiar_estado_caso(8, "inventado", confirmado=True)


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_cambia_el_estado_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    ruta = respx.put(f"{CASOS_BASE_URL}/cases/8").mock(return_value=httpx.Response(200, json=_CASO_ACTUALIZADO))

    resultado = await cambiar_estado_caso(8, "en_progreso", confirmado=True)

    assert resultado == {"estado": "ok", "datos": _CASO_ACTUALIZADO}
    import json as _json

    assert _json.loads(ruta.calls.last.request.content) == {"estado": "en_progreso"}


# --- no encontrado -----------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/999").mock(
        return_value=httpx.Response(404, json={"detail": "Caso no encontrado"})
    )

    resultado = await cambiar_estado_caso(999, "en_progreso", confirmado=True)

    assert resultado == {"estado": "no_encontrado", "detalle": "Caso no encontrado"}


# --- conflicto (409, tres causas posibles) ---------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_transicion_no_permitida_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(
        return_value=httpx.Response(
            409, json={"detail": "Transición de estado no permitida: archivado -> abierto"}
        )
    )

    resultado = await cambiar_estado_caso(8, "abierto", confirmado=True)

    assert resultado == {
        "estado": "conflicto",
        "detalle": "Transición de estado no permitida: archivado -> abierto",
    }


@pytest.mark.asyncio
@respx.mock
async def test_caso_archivado_es_conflicto_con_el_detalle_real():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(
        return_value=httpx.Response(
            409, json={"detail": "El caso está archivado: es un registro histórico inmutable"}
        )
    )

    resultado = await cambiar_estado_caso(8, "cerrado", confirmado=True)

    assert resultado["estado"] == "conflicto"
    assert "archivado" in resultado["detalle"]


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
    peticion = respx.put(f"{CASOS_BASE_URL}/cases/8").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_CASO_ACTUALIZADO),
        ]
    )

    resultado = await cambiar_estado_caso(8, "en_progreso", confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await cambiar_estado_caso(8, "en_progreso", confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(
        return_value=httpx.Response(422, json={"detail": "estado inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await cambiar_estado_caso(8, "en_progreso", confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await cambiar_estado_caso(8, "en_progreso", confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await cambiar_estado_caso(8, "en_progreso", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.put(f"{CASOS_BASE_URL}/cases/8").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await cambiar_estado_caso(8, "en_progreso", confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Casos local (SIN mocks). Crea su PROPIO caso de prueba
# (vía crear_caso, ya validada en tests/test_crear_caso.py) para no depender
# de ningún caso preexistente, y le cambia el estado de verdad dos veces
# (abierto -> en_progreso -> cerrado, ambas transiciones válidas según
# TRANSICIONES_VALIDAS), comprobando la respuesta real en cada paso. El caso
# creado queda documentado (prefijo "MCP-TEST-Fase2G-cambiar_estado_caso-")
# para poder localizarlo después.
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_casos_local_si_esta_disponible():
    import os
    from datetime import datetime, timezone

    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    from app.main import crear_caso

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre = f"MCP-TEST-Fase2G-cambiar_estado_caso-{marca}"

    try:
        creado = await crear_caso(nombre, "MCP Server (test automático)", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert creado["estado"] == "ok"
    case_id = creado["datos"]["id"]
    assert creado["datos"]["estado"] == "abierto"

    a_en_progreso = await cambiar_estado_caso(case_id, "en_progreso", confirmado=True)
    assert a_en_progreso["estado"] == "ok"
    assert a_en_progreso["datos"]["estado"] == "en_progreso"

    a_cerrado = await cambiar_estado_caso(case_id, "cerrado", confirmado=True)
    assert a_cerrado["estado"] == "ok"
    assert a_cerrado["datos"]["estado"] == "cerrado"

    print(
        f"\n[test_real_contra_casos_local_si_esta_disponible] Caso de prueba "
        f"id={case_id} nombre={nombre!r} — abierto -> en_progreso -> cerrado, verificado."
    )
