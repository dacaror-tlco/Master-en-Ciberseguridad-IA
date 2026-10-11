"""
conftest.py de los tests de Timeline. Fija DATABASE_URL a una SQLite
temporal ANTES de que app.core.database se importe, y crea a mano (con
SQL plano, no ORM) las tablas de las que Timeline lee pero no posee
(evidences, tracking_events, osint_findings) — igual que en la base
compartida real, son propiedad de otros backends; aquí solo se recrea su
forma mínima para poder probar Timeline en aislamiento, nunca se importa
su modelo Python. `cases` es la excepción: necesita un mínimo declarado
en el mismo MetaData de SQLAlchemy (ver SharedCaseRow) solo para que
`create_all()` pueda resolver la FK de timeline_events, no para que
Timeline la gestione.
"""

import os
import tempfile

_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"

# Fase final (hardening): fija también JWT_SECRET ANTES de que
# app.modules.auth.security lo lea (constante de módulo, se fija en el
# primer import) — evita el InsecureKeyLengthWarning de pyjwt que daba el
# valor por defecto "change_me" (9 bytes). Secreto ficticio, nunca real;
# no toca ningún .env.
os.environ["JWT_SECRET"] = "solo-para-tests-nunca-un-secreto-real-0123456789abcdef"

import sqlite3  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Column, Integer, String  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.timeline import models as _timeline_models  # noqa: E402,F401


class SharedCaseRow(Base):
    """
    `cases` MÍNIMA, solo para que `Base.metadata.create_all()` pueda
    resolver la FK de `timeline_events.case_id` en esta SQLite aislada de
    test (SQLAlchemy exige que la tabla referenciada exista en el mismo
    MetaData, aunque este backend no la posea). NO es el modelo de Casos
    — vive solo aquí y nunca se importa desde app/. Los datos de prueba
    reales se insertan con SQL plano (ver _seed_multi_source_case), no a
    través de esta clase.
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150))
    estado = Column(String(30))
    responsable = Column(String(100))

_SOURCE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS evidences (
    id INTEGER PRIMARY KEY, case_id INTEGER, tipo TEXT, valor TEXT,
    fecha_subida TEXT, observaciones TEXT,
    fecha_adquisicion TEXT, eliminado INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tracking_events (
    id INTEGER PRIMARY KEY, case_id INTEGER, hora TEXT, evento TEXT,
    severidad TEXT, fuente_log TEXT, usuario_detectado TEXT
);
CREATE TABLE IF NOT EXISTS osint_findings (
    id INTEGER PRIMARY KEY, case_type TEXT, source_table TEXT, source_id INTEGER,
    case_id INTEGER, subject_type TEXT, subject_value TEXT, risk_score INTEGER,
    risk_level TEXT, headline TEXT, flag_count INTEGER, top_flags TEXT,
    details TEXT, analyzed_at TEXT, created_at TEXT
);
"""


@pytest.fixture(autouse=True)
def clean_database_between_tests():
    Base.metadata.drop_all(bind=engine)  # borra solo timeline_events (lo único en Base.metadata)
    Base.metadata.create_all(bind=engine)
    conn = sqlite3.connect(_tmp_db_path)
    conn.executescript(_SOURCE_TABLES_SQL)
    conn.executescript(
        "DELETE FROM cases; DELETE FROM evidences; "
        "DELETE FROM tracking_events; DELETE FROM osint_findings;"
    )
    conn.commit()
    conn.close()
    yield


def _bearer_token(*, role: str = "analyst") -> str:
    from datetime import datetime, timedelta, timezone

    import jwt

    from app.modules.auth.security import JWT_SECRET

    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + timedelta(hours=1)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def client():
    """
    Fase 4: los 2 endpoints de este backend exigen autenticación, sin
    excepciones. Llega ya con un JWT de analyst válido por defecto —
    igual que el resto de la suite, que prueba lógica de negocio, no
    auth en sí (eso vive en test_auth_timeline.py, con un cliente sin
    esta cabecera).
    """
    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {_bearer_token()}"
        yield c


@pytest.fixture
def raw_conn():
    conn = sqlite3.connect(_tmp_db_path)
    yield conn
    conn.close()
