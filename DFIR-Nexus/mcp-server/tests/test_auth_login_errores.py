"""
Tests de `CasosSession._login` (app/core/auth.py) para errores de
autenticación DISTINTOS de 401 — encontrados en la auditoría final
(Fase 2A-2I): antes de esta fase, un fallo de Casos al autenticar que no
fuera exactamente 401 (p. ej. un 500 transitorio, o cualquier otro código)
llegaba a `response.raise_for_status()`, que lanza `httpx.HTTPStatusError`
— una excepción que NINGÚN llamador capturaba: ni `_login` (no tenía
`try/except` para ese caso), ni `_peticion_segura` en app/main.py (solo
captura `CasosAuthError` y `httpx.RequestError`, y `HTTPStatusError` es
una subclase HERMANA de `RequestError` bajo `httpx.HTTPError`, no una
subclase de ella). El resultado: la tool completa fallaba con una
excepción cruda sin envolver, en vez de un `ToolError` claro como
cualquier otro fallo de este proceso.

Esto afectaba a las VEINTIDÓS tools por igual (todas pasan por
`casos_session.request`, que llama a `_login` en la primera petición del
proceso o tras un 401) — no es un fallo de una tool concreta, es del
núcleo de autenticación compartido.

Corrección: `_login` ahora comprueba explícitamente
`response.status_code != 200` (además del caso 401 ya existente) y
lanza `CasosAuthError` en ambos casos, nunca `raise_for_status()` —
`CasosAuthError` SÍ la captura `_peticion_segura` y la envuelve en
`ToolError`, igual que cualquier otro fallo de autenticación.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from app.core.auth import CasosAuthError
from app.core.http_client import casos_session
from app.main import consultar_caso

CASOS_BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
@respx.mock
async def test_login_con_500_se_envuelve_en_toolerror_no_en_httpstatuserror():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(500, json={"detail": "Error interno"})
    )

    # Antes de la corrección, esto lanzaba httpx.HTTPStatusError (sin
    # envolver) en vez de ToolError — el `match` además confirma que el
    # mensaje es el mismo camino ya usado para cualquier otro fallo de
    # autenticación (No se ha podido autenticar contra Casos: ...).
    with pytest.raises(ToolError, match="No se ha podido autenticar contra Casos"):
        await consultar_caso(8)


@pytest.mark.asyncio
@respx.mock
async def test_login_con_422_tambien_se_envuelve_en_toolerror():
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(422, json={"detail": "cuerpo inválido"})
    )

    with pytest.raises(ToolError, match="No se ha podido autenticar contra Casos"):
        await consultar_caso(8)


@pytest.mark.asyncio
@respx.mock
async def test_login_con_500_directamente_sobre_casossession_lanza_casosautherror():
    """Prueba unitaria más directa, sin pasar por una tool: `_login` en sí
    misma debe traducir el 500 a `CasosAuthError`, no dejar escapar
    `httpx.HTTPStatusError`."""
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(return_value=httpx.Response(503))

    with pytest.raises(CasosAuthError, match="503"):
        await casos_session._login()
