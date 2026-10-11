"""
Configuración de la base de datos: MySQL, mismo patrón que el resto de
módulos de Nexus (ver modulo-casos/backend/app/core/database.py).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite (solo dev local vía DB_URL) se toca desde varios hilos: el worker de
# uvicorn y el scheduler en proceso (APScheduler). check_same_thread=False lo
# permite; para MySQL este connect_args va vacío y no cambia nada.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia de FastAPI: abre una sesión por petición y la cierra siempre al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
