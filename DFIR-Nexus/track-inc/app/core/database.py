"""
Conexión a base de datos compartida por todos los módulos de Nexus.

Todos los modelos (cases, evidences, osint_results, tracking_events,
timeline_events, reports) deben usar esta misma `Base` para que
SQLAlchemy/Alembic vean un único metadata consistente al generar
migraciones, aunque cada módulo viva en su propia carpeta.

El motor oficial del proyecto es MySQL (ver CLAUDE.md), con el driver
`pymysql`. La conexión se resuelve en este orden:

  1. `DATABASE_URL` si está definida (permite SQLite en local y en tests).
  2. Las variables `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`,
     `MYSQL_PASSWORD` y `MYSQL_DB` del fichero `.env`, que es el patrón
     que usan los demás módulos de Nexus.
  3. Un MySQL local, como último recurso.

El `.env` NO se versiona (está en `.gitignore`) y contiene credenciales:
nunca debe acabar en el repositorio ni en el zip del entregable.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# El .env vive en la raíz del módulo (dos niveles por encima de app/core/).
# override=False: si la variable ya viene del entorno, manda esa.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

DEFAULT_DATABASE_URL = "mysql+pymysql://nexus:nexus@localhost:3306/nexus"


def _url_desde_variables_mysql() -> str | None:
    """Construye la URL a partir de las variables MYSQL_* del .env.

    Devuelve None si falta alguna, para caer al siguiente candidato en vez
    de intentar conectar con una URL a medias.
    """
    host = os.environ.get("MYSQL_HOST")
    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    base = os.environ.get("MYSQL_DB")
    puerto = os.environ.get("MYSQL_PORT", "3306")

    if not all([host, user, password, base]):
        return None

    # quote_plus por si la contraseña trae caracteres que romperían la URL
    # (@, :, /, #...). Es un fallo clásico y silencioso.
    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{puerto}/{base}"


DATABASE_URL = os.environ.get("DATABASE_URL") or _url_desde_variables_mysql() or DEFAULT_DATABASE_URL


def _connect_args_para(url: str) -> dict:
    """Argumentos de conexión propios de cada motor."""
    if url.startswith("sqlite"):
        # necesario para usar SQLite en tests con TestClient, que accede
        # desde hilos distintos
        return {"check_same_thread": False}

    if url.startswith("mysql"):
        # Los MySQL gestionados (Aiven, PlanetScale...) exigen TLS. Si se
        # indica la CA del proveedor se verifica el certificado, que es lo
        # correcto; si no, se cifra igualmente pero sin verificar. Para un
        # MySQL local en la propia máquina no hace falta nada.
        ca = os.environ.get("MYSQL_SSL_CA")
        if ca:
            return {"ssl": {"ca": ca}}
        if os.environ.get("MYSQL_SSL", "auto").lower() == "false":
            return {}
        es_local = any(h in url for h in ("@localhost", "@127.0.0.1"))
        return {} if es_local else {"ssl": {}}

    return {}


engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args_para(DATABASE_URL),
    # los servidores gestionados cierran conexiones ociosas; sin esto
    # aparecen errores intermitentes de "MySQL server has gone away"
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Base declarativa única para todos los módulos."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: una sesión por request, cerrada al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
