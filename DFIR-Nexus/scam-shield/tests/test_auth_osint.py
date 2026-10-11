"""
Fase 4: autenticación aplicada a los 44 endpoints de OSINT (a nivel de
router, ver app/main.py), salvo la única excepción técnica identificada
(GET /analysis/image/preview/{token}, que debe seguir siendo público).
No repite la lógica de negocio de cada submódulo (ya cubierta por el
resto de la suite, que usa el `client` autenticado de conftest.py): esto
prueba únicamente la capa de autenticación/autorización añadida encima.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def anon_client():
    """Mismo montaje que el `client` de conftest.py, pero SIN ninguna
    cabecera Authorization por defecto — para probar los escenarios
    401 propiamente dichos."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _token(*, role: str = "analyst", exp_delta: timedelta = timedelta(hours=1)) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + exp_delta}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def test_endpoint_protegido_sin_token_es_401(anon_client):
    r = anon_client.get("/domain-analysis-cases")
    assert r.status_code == 401


def test_token_invalido_es_401(anon_client):
    r = anon_client.get("/domain-analysis-cases", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_token_expirado_es_401(anon_client):
    token = _token(exp_delta=timedelta(hours=-1))
    r = anon_client.get("/domain-analysis-cases", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_analyst_con_token_valido_accede(anon_client):
    r = anon_client.get(
        "/domain-analysis-cases", headers={"Authorization": f"Bearer {_token(role='analyst')}"}
    )
    assert r.status_code == 200


def test_admin_con_token_valido_tambien_accede(anon_client):
    """admin = analyst + administrativas; OSINT no distingue entre ambos
    porque no tiene ningún endpoint admin-only (ver matriz de permisos)."""
    r = anon_client.get(
        "/domain-analysis-cases", headers={"Authorization": f"Bearer {_token(role='admin')}"}
    )
    assert r.status_code == 200


def test_preview_de_imagen_sigue_siendo_publico_sin_ningun_token(anon_client):
    """Única excepción técnica: SerpApi la consume por URL, sin poder
    llevar cabecera Authorization. No debe devolver 401 — un token
    opaco inexistente/caducado da 404, que es el comportamiento normal
    de este endpoint, no un fallo de autenticación."""
    r = anon_client.get("/analysis/image/preview/token-inexistente")
    assert r.status_code == 404
    assert r.status_code != 401


def test_health_sigue_siendo_publico(anon_client):
    r = anon_client.get("/health")
    assert r.status_code == 200
