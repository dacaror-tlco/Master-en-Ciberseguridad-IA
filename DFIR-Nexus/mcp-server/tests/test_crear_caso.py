"""
Tests de la tool `crear_caso` (Fase 2G, Casos) — segunda tool de escritura
del MCP Server, primera que crea un recurso nuevo (no modifica uno
existente).

`POST /cases` (backend/app/modules/cases/routes.py) verificado en el
código real:
- Solo exige `get_current_user` (cualquier analyst autenticado, no admin).
- `nombre`/`responsable` son obligatorios en el esquema (`CaseBase`);
  `descripcion` es opcional; `estado` es opcional y por defecto
  `EstadoCaso.ABIERTO` si no se envía (`CaseCreate.estado`).
- Sin validación propia de "no vacío" en el esquema — por eso esta tool
  valida nombre/responsable no vacíos ANTES de llamar al backend (ver
  enunciado: "Valida parámetros antes de llamar al backend").
- No hay ningún conflicto de dominio posible al crear (no hay nombres
  únicos): el único error real documentado, aparte de 401/422/5xx
  genéricos, sería un 422 de pydantic si algo se cuela sin validar aquí.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import crear_caso

CASOS_BASE_URL = "http://localhost:8000"

_CASO_CREADO = {
    "id": 42,
    "nombre": "Caso de prueba",
    "descripcion": None,
    "responsable": "Yolanda",
    "estado": "abierto",
    "fecha_creacion": "2026-09-29T10:00:00",
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
        await crear_caso("Caso de prueba", "Yolanda", confirmado=False)


@pytest.mark.asyncio
async def test_nombre_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="nombre"):
        await crear_caso("   ", "Yolanda", confirmado=True)
    with pytest.raises(ToolError, match="nombre"):
        await crear_caso("", "Yolanda", confirmado=False)


@pytest.mark.asyncio
async def test_responsable_vacio_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="responsable"):
        await crear_caso("Caso de prueba", "  ", confirmado=True)


@pytest.mark.asyncio
async def test_estado_invalido_se_rechaza_antes_que_confirmado():
    with pytest.raises(ToolError, match="abierto"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True, estado="inventado")


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_crea_el_caso_y_devuelve_los_datos_reales():
    _mockear_login_ok()
    ruta = respx.post(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(201, json=_CASO_CREADO))

    resultado = await crear_caso("Caso de prueba", "Yolanda", confirmado=True)

    assert resultado == {"estado": "ok", "datos": _CASO_CREADO}
    enviado = ruta.calls.last.request
    import json as _json

    cuerpo = _json.loads(enviado.content)
    assert cuerpo == {"nombre": "Caso de prueba", "responsable": "Yolanda", "descripcion": None}
    assert "estado" not in cuerpo  # sin estado explícito: el backend decide el valor por defecto


@pytest.mark.asyncio
@respx.mock
async def test_confirmado_true_con_estado_y_descripcion_los_envia_tal_cual():
    _mockear_login_ok()
    ruta = respx.post(f"{CASOS_BASE_URL}/cases").mock(
        return_value=httpx.Response(201, json={**_CASO_CREADO, "estado": "en_progreso", "descripcion": "Notas"})
    )

    resultado = await crear_caso(
        "Caso de prueba", "Yolanda", confirmado=True, descripcion="Notas", estado="en_progreso"
    )

    assert resultado["estado"] == "ok"
    import json as _json

    cuerpo = _json.loads(ruta.calls.last.request.content)
    assert cuerpo == {
        "nombre": "Caso de prueba",
        "responsable": "Yolanda",
        "descripcion": "Notas",
        "estado": "en_progreso",
    }


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
    peticion = respx.post(f"{CASOS_BASE_URL}/cases").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(201, json=_CASO_CREADO),
        ]
    )

    resultado = await crear_caso("Caso de prueba", "Yolanda", confirmado=True)

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(401, json={"detail": "No autenticado"}))

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True)


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases").mock(
        return_value=httpx.Response(422, json={"detail": "nombre inválido"})
    )

    with pytest.raises(ToolError, match="422"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True)


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True)


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.post(f"{CASOS_BASE_URL}/cases").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await crear_caso("Caso de prueba", "Yolanda", confirmado=True)


# -----------------------------------------------------------------------------
# Prueba real contra Casos local (SIN mocks). Crea un caso de prueba REAL y
# claramente identificable (prefijo "MCP-TEST-Fase2G-crear_caso-", con marca
# de tiempo) para poder localizarlo y, si se desea, borrarlo manualmente
# después — esta fase no expone ninguna tool de borrado de casos a propósito
# (ver enunciado: "No expongas DELETE de casos"). No se borra nada aquí.
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

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre = f"MCP-TEST-Fase2G-crear_caso-{marca}"

    try:
        resultado = await crear_caso(
            nombre,
            "MCP Server (test automático)",
            confirmado=True,
            descripcion="Caso de prueba creado por tests/test_crear_caso.py — seguro de borrar manualmente.",
        )
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    datos = resultado["datos"]
    assert datos["nombre"] == nombre
    assert datos["responsable"] == "MCP Server (test automático)"
    assert datos["estado"] == "abierto"
    assert datos["eliminado"] is False

    print(f"\n[test_real_contra_casos_local_si_esta_disponible] Caso de prueba creado: id={datos['id']} nombre={nombre!r}")
