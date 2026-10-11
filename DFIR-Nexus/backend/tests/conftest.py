"""
Fixtures compartidas. Mismo patrón que scam-shield/sharingan: una SQLite en
memoria exclusiva de cada test, con el motor real (MySQL/Aiven, creado de
forma perezosa en app.core.database) nunca tocado porque get_db se
sustituye por completo vía dependency_overrides.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.modules.auth.models import Rol, User
from app.modules.auth.security import hash_password
from app.modules.cases.integrity import calcular_hash_valor
from app.modules.cases.models import Case, EstadoCaso, Evidence

PASSWORD_PRUEBA = "contraseña-de-prueba-123"

# Fase final (hardening): el JWT_SECRET real de .env puede no estar
# definido (cae al default "change_me", de 9 bytes) o, si lo está, no
# debe usarse en tests. En ambos casos pyjwt avisaba con
# InsecureKeyLengthWarning al firmar/verificar con una clave < 32 bytes.
# Se sobreescribe aquí, en memoria, el único Settings singleton del
# proceso de test — NUNCA se toca el .env real ni se usa un secreto real.
settings.JWT_SECRET = "solo-para-tests-nunca-un-secreto-real-0123456789abcdef"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _base_datos_limpia():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def caso(db_session) -> Case:
    case = Case(
        nombre="Intrusión en servidor web",
        estado=EstadoCaso.ABIERTO,
        descripcion="Acceso no autorizado detectado por el SIEM",
        responsable="Ana Pérez",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def _crear_usuario(db_session, *, nombre: str, email: str, rol: Rol, activo: bool = True) -> User:
    user = User(
        nombre=nombre,
        email=email,
        password_hash=hash_password(PASSWORD_PRUEBA),
        rol=rol,
        activo=activo,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin(db_session) -> User:
    return _crear_usuario(db_session, nombre="Admin Uno", email="admin@nexus.local", rol=Rol.ADMIN)


@pytest.fixture
def analyst(db_session) -> User:
    return _crear_usuario(db_session, nombre="Analyst Uno", email="analyst@nexus.local", rol=Rol.ANALYST)


def auth_headers(client, email: str, password: str = PASSWORD_PRUEBA) -> dict:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def evidencia(db_session, caso) -> Evidence:
    valor = "203.0.113.10"
    evidence = Evidence(
        case_id=caso.id,
        tipo="ip",
        valor=valor,
        hash_valor=calcular_hash_valor(valor),
        fecha_adquisicion=datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc).replace(tzinfo=None),
        observaciones="Detectada en el firewall perimetral",
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return evidence
