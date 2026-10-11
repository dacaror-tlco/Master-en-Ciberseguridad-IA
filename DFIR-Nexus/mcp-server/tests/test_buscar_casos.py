"""
Tests de la tool `buscar_casos` (Fase 2A).

Mismo criterio que test_consultar_caso.py: HTTP hacia Casos interceptado
con respx, el fixture `_sesion_sin_token` de conftest.py resetea el JWT en
memoria entre tests.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.main import buscar_casos

CASOS_BASE_URL = "http://localhost:8000"

_CASOS_DE_EJEMPLO = [
    {
        "id": 1,
        "nombre": "Intrusión servidor web",
        "descripcion": "Acceso no autorizado vía CVE conocido",
        "responsable": "Yolanda",
        "estado": "abierto",
        "fecha_creacion": "2026-01-01T00:00:00",
        "fecha_actualizacion": "2026-01-01T00:00:00",
        "eliminado": False,
        "fecha_eliminacion": None,
    },
    {
        "id": 2,
        "nombre": "Fuga de datos RRHH",
        "descripcion": None,
        "responsable": "Marcos",
        "estado": "cerrado",
        "fecha_creacion": "2026-01-02T00:00:00",
        "fecha_actualizacion": "2026-01-02T00:00:00",
        "eliminado": False,
        "fecha_eliminacion": None,
    },
    {
        "id": 3,
        "nombre": "Ransomware en filial",
        "descripcion": "Cifrado masivo detectado por EDR",
        "responsable": "Yolanda",
        "estado": "en_progreso",
        "fecha_creacion": "2026-01-03T00:00:00",
        "fecha_actualizacion": "2026-01-03T00:00:00",
        "eliminado": False,
        "fecha_eliminacion": None,
    },
]


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


def _mockear_lista_casos(casos: list[dict] = _CASOS_DE_EJEMPLO) -> respx.Route:
    return respx.get(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(200, json=casos))


# --- sin filtros --------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_sin_filtros_devuelve_todos():
    _mockear_login_ok()
    _mockear_lista_casos()

    resultado = await buscar_casos()

    assert resultado["estado"] == "ok"
    assert resultado["datos"]["total"] == 3
    assert [c["id"] for c in resultado["datos"]["casos"]] == [1, 2, 3]


# --- filtro por estado ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_filtro_por_estado():
    _mockear_login_ok()
    _mockear_lista_casos()

    resultado = await buscar_casos(estado="abierto")

    assert resultado["datos"]["total"] == 1
    assert resultado["datos"]["casos"][0]["id"] == 1


# --- filtro por texto ------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_filtro_por_texto_busca_en_nombre_responsable_y_descripcion():
    _mockear_login_ok()
    _mockear_lista_casos()

    # Coincide por "nombre" (case-insensitive)
    resultado = await buscar_casos(texto="ransomware")
    assert resultado["datos"]["total"] == 1
    assert resultado["datos"]["casos"][0]["id"] == 3

    # Coincide por "responsable"
    resultado = await buscar_casos(texto="yolanda")
    assert {c["id"] for c in resultado["datos"]["casos"]} == {1, 3}

    # Coincide por "descripcion"
    resultado = await buscar_casos(texto="CVE")
    assert resultado["datos"]["total"] == 1
    assert resultado["datos"]["casos"][0]["id"] == 1


# --- ambos filtros (AND lógico) -------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_ambos_filtros_aplican_and_logico():
    _mockear_login_ok()
    _mockear_lista_casos()

    # "Yolanda" está en los casos 1 (abierto) y 3 (en_progreso); con
    # estado="abierto" solo debe quedar el 1.
    resultado = await buscar_casos(estado="abierto", texto="yolanda")

    assert resultado["datos"]["total"] == 1
    assert resultado["datos"]["casos"][0]["id"] == 1


# --- lista vacía -----------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_sin_coincidencias_devuelve_lista_vacia_no_error():
    _mockear_login_ok()
    _mockear_lista_casos()

    resultado = await buscar_casos(texto="no existe ningún caso con esto")

    assert resultado["estado"] == "ok"
    assert resultado["datos"] == {"total": 0, "casos": []}


@pytest.mark.asyncio
@respx.mock
async def test_backend_sin_casos_devuelve_lista_vacia():
    _mockear_login_ok()
    _mockear_lista_casos(casos=[])

    resultado = await buscar_casos()

    assert resultado["datos"] == {"total": 0, "casos": []}


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
    peticion = respx.get(f"{CASOS_BASE_URL}/cases").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_CASOS_DE_EJEMPLO),
        ]
    )

    resultado = await buscar_casos()

    assert resultado["datos"]["total"] == 3
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(401, json={"detail": "No autenticado"}))

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await buscar_casos()


# --- 5xx -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro():
    _mockear_login_ok()
    respx.get(f"{CASOS_BASE_URL}/cases").mock(return_value=httpx.Response(503))

    with pytest.raises(ToolError, match="error del servidor"):
        await buscar_casos()


# --- error de conexión ---------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await buscar_casos()


# --- entradas inválidas ---------------------------------------------------


@pytest.mark.asyncio
async def test_estado_invalido_se_rechaza_sin_llamar_a_casos():
    with pytest.raises(ToolError, match="no es válido"):
        await buscar_casos(estado="en-proceso")  # guion en vez de guion bajo, valor real inexistente


@pytest.mark.asyncio
@respx.mock
async def test_texto_en_blanco_se_trata_como_sin_filtro():
    _mockear_login_ok()
    _mockear_lista_casos()

    resultado = await buscar_casos(texto="   ")

    assert resultado["datos"]["total"] == 3


# -----------------------------------------------------------------------------
# Prueba real contra el backend de Casos local (SIN mocks). Se salta si no hay
# credenciales en el entorno, o si Casos no responde — nunca hardcodeadas
# aquí, y nunca crea/modifica nada: solo lee /cases.
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

    try:
        resultado = await buscar_casos()
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    assert "total" in resultado["datos"]
    assert isinstance(resultado["datos"]["casos"], list)
