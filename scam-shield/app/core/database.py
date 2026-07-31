"""
Configuración de la base de datos.

Usamos SQLAlchemy como capa intermedia precisamente para que cambiar de
SQLite (desarrollo) a PostgreSQL (producción) sea solo cambiar la
variable de entorno DATABASE_URL, sin tocar ni una línea del resto
del código.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# connect_args solo es necesario para SQLite (permite usarlo desde varios
# hilos, cosa que FastAPI hace por defecto). Con PostgreSQL no hace falta
# y lo quitaremos cuando migremos.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
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
