"""
Fase 4: autenticación aplicada a los 5 endpoints de este backend (a nivel
de router, ver app/main.py). No repite la lógica de negocio (ya cubierta
por el resto de la suite, que usa el `client` autenticado de
conftest.py): esto prueba únicamente la capa de autenticación/
autorización añadida encima. No hay endpoints admin en este backend (ver
matriz de permisos, Fase 4), así que no hay escenarios 403 que probar
aquí. `/health` sigue público.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


def _token(*, role: str = "analyst", exp_delta: timedelta = timedelta(hours=1)) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + exp_delta}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@pytest.fixture
def anon_client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_generate_sin_token_es_401(anon_client):
    r = anon_client.post("/reports/generate", json={"case_id": 1, "generado_por": "Ana"})
    assert r.status_code == 401


def test_get_report_sin_token_es_401(anon_client):
    assert anon_client.get("/reports/1").status_code == 401


def test_list_for_case_sin_token_es_401(anon_client):
    assert anon_client.get("/cases/1/reports").status_code == 401


def test_token_invalido_es_401(anon_client):
    r = anon_client.get("/reports/1", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_token_caducado_es_401(anon_client):
    token = _token(exp_delta=timedelta(hours=-1))
    r = anon_client.get("/reports/1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_analyst_con_token_valido_accede(anon_client):
    r = anon_client.get("/reports/1", headers={"Authorization": f"Bearer {_token(role='analyst')}"})
    assert r.status_code == 404  # autenticado, pero el informe 1 no existe: pasó la autorización


def test_admin_con_token_valido_tambien_accede(anon_client):
    r = anon_client.get("/reports/1", headers={"Authorization": f"Bearer {_token(role='admin')}"})
    assert r.status_code == 404


def test_health_sigue_siendo_publico(anon_client):
    assert anon_client.get("/health").status_code == 200
