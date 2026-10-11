"""
Fase 4: autenticación aplicada a los 2 endpoints de este backend (a nivel
de router, ver app/main.py). No repite la lógica de negocio (ya cubierta
por test_routes.py, que usa el `client` autenticado de conftest.py): esto
prueba únicamente la capa de autenticación/autorización añadida encima.
No hay endpoints admin en este backend (ver matriz de permisos, Fase 4),
así que no hay escenarios 403 que probar aquí. `/health` sigue público.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.security import JWT_SECRET


def _token(*, role: str = "analyst", exp_delta: timedelta = timedelta(hours=1)) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + exp_delta}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def anon_client():
    with TestClient(app) as c:
        yield c


def test_get_timeline_sin_token_es_401(anon_client):
    assert anon_client.get("/timeline/cases/1").status_code == 401


def test_refresh_sin_token_es_401(anon_client):
    assert anon_client.post("/timeline/cases/1/refresh").status_code == 401


def test_token_invalido_es_401(anon_client):
    r = anon_client.get("/timeline/cases/1", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_token_caducado_es_401(anon_client):
    token = _token(exp_delta=timedelta(hours=-1))
    r = anon_client.get("/timeline/cases/1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_analyst_con_token_valido_accede(anon_client):
    r = anon_client.get("/timeline/cases/1", headers={"Authorization": f"Bearer {_token(role='analyst')}"})
    assert r.status_code == 200


def test_admin_con_token_valido_tambien_accede(anon_client):
    r = anon_client.get("/timeline/cases/1", headers={"Authorization": f"Bearer {_token(role='admin')}"})
    assert r.status_code == 200


def test_health_sigue_siendo_publico(anon_client):
    assert anon_client.get("/health").status_code == 200
