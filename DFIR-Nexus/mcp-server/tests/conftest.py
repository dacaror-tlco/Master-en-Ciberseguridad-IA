"""Fixtures compartidas por todos los tests de tools MCP contra Casos."""

from __future__ import annotations

import pytest

from app.core.http_client import casos_session

CASOS_BASE_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def _sesion_sin_token():
    """Cada test empieza sin JWT en memoria.

    `casos_session` es el singleton de módulo que usan las tools reales
    (mismo objeto que en producción, para probar el camino real y no una
    copia). Si un test anterior hizo login con éxito, sin este reset el
    siguiente test heredaría el token y no vería lo que dice estar
    comprobando (p. ej. el test del primer login).
    """
    casos_session._token = None
    yield
    casos_session._token = None
