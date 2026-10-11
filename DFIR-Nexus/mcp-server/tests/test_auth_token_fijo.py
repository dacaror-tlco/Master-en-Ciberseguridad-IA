"""
Tests de `MCP_ACCESS_TOKEN` (app/core/config.py): un JWT ya emitido con el
que el proceso actúa sin iniciar sesión nunca.

Es el modo en que lo lanza el asistente de Informes, con el token del
analista que pregunta. Lo que importa comprobar es lo que NO hace: no llama
a /auth/login ni en la primera petición ni tras un 401, porque con ese
modo no hay credenciales de servicio con las que hacerlo.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.core import auth
from app.core.auth import CasosSession

CASOS_BASE_URL = "http://localhost:8000"


@pytest.fixture
def sesion_con_token(monkeypatch):
    monkeypatch.setattr(auth.settings, "MCP_ACCESS_TOKEN", "jwt-del-analista")
    return CasosSession(httpx.AsyncClient(base_url=CASOS_BASE_URL))


@pytest.mark.asyncio
@respx.mock
async def test_usa_el_token_dado_sin_iniciar_sesion(sesion_con_token):
    login = respx.post(f"{CASOS_BASE_URL}/auth/login")
    caso = respx.get(f"{CASOS_BASE_URL}/cases/8").mock(return_value=httpx.Response(200, json={}))

    await sesion_con_token.request("GET", "/cases/8")

    assert not login.called
    assert caso.calls.last.request.headers["authorization"] == "Bearer jwt-del-analista"


@pytest.mark.asyncio
@respx.mock
async def test_un_401_con_token_dado_sube_tal_cual_sin_reintentar(sesion_con_token):
    login = respx.post(f"{CASOS_BASE_URL}/auth/login")
    caso = respx.get(f"{CASOS_BASE_URL}/cases/8").mock(return_value=httpx.Response(401))

    response = await sesion_con_token.request("GET", "/cases/8")

    assert response.status_code == 401
    assert not login.called
    assert caso.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_sin_token_dado_sigue_iniciando_sesion(monkeypatch):
    monkeypatch.setattr(auth.settings, "MCP_ACCESS_TOKEN", "")
    sesion = CasosSession(httpx.AsyncClient(base_url=CASOS_BASE_URL))
    login = respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(200, json={"access_token": "de-servicio"})
    )
    respx.get(f"{CASOS_BASE_URL}/cases/8").mock(return_value=httpx.Response(200, json={}))

    await sesion.request("GET", "/cases/8")

    assert login.called
