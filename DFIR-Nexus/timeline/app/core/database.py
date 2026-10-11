"""
Conexión a base de datos de este backend (Timeline).

Timeline es un backend independiente (ver docs/CONTRATOS.md): comparte la
base MySQL con Casos, OSINT y Tracking, pero no comparte código Python ni
proceso con ellos. `Base` aquí solo declara `timeline_events` — Timeline
NUNCA importa los modelos de otros backends para leer `cases`,
`evidences`, `osint_findings` o `tracking_events`; esas lecturas se hacen
con SQL directo y mínimo (ver app/modules/timeline/repository.py).

DATABASE_URL por defecto apunta a MySQL (motor oficial, ver CLAUDE.md);
para desarrollo local sin servidor se puede sobreescribir con SQLite vía
la variable de entorno DATABASE_URL — mismo patrón que Tracking.

`load_dotenv()` carga `timeline/.env` (si existe) antes de leer
DATABASE_URL de `os.environ` — mismo fix y mismo mecanismo que
track-inc/app/core/database.py: sin esto, DATABASE_URL nunca llegaba a
`os.environ` al arrancar `uvicorn` normal y el backend caía siempre en
DEFAULT_DATABASE_URL sin avisar. Se apunta al `.env` por ruta absoluta
(no al cwd) para que el resultado no dependa de desde dónde se lance
uvicorn/alembic. `override=False` (por defecto) es imprescindible: si
DATABASE_URL ya está en el entorno —como hacen los tests, o un `export`
explícito— `.env` no debe pisarlo.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_DATABASE_URL = "mysql+pymysql://nexus:nexus@localhost:3306/nexus"

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
