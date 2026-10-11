from logging.config import fileConfig
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# permite importar `app.*` al correr alembic desde la raíz de este backend
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Carga timeline/.env por ruta absoluta antes de leer DATABASE_URL más
# abajo — mismo motivo y mismo mecanismo que app/core/database.py (el
# import que sigue ya lo hace también, pero se repite aquí explícitamente
# porque este módulo lee `os.environ` directamente). override=False: no
# debe pisar una DATABASE_URL ya presente en el entorno.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.core.database import Base  # noqa: E402
# Solo se registra el modelo que este backend posee (timeline_events).
# `cases`/`evidences` de la migración 0001 (bootstrap propio, ver esa
# migración) no tienen modelo aquí a propósito: este backend no las
# gestiona ni las lee vía ORM, solo con SQL directo.
from app.modules.timeline import models as _timeline_models  # noqa: E402,F401

config = context.config

db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

#: Tablas que este backend (Timeline) posee. Su Alembic solo puede
#: gestionar esta.
TABLAS_PROPIAS = frozenset({"timeline_events"})

#: `development` comparte una única base MySQL entre los cinco backends.
#: Timeline sella su propio historial en su propia tabla de versiones, no
#: en el `alembic_version` por defecto, para no pisarse con el Alembic de
#: otro backend apuntando a la misma base — mismo criterio que Casos
#: (alembic_version_casos), OSINT (alembic_version_scamshield), Tracking
#: (alembic_version_tracking) e Informes (alembic_version_sharingan).
#:
#: IMPORTANTE (Fase 3, sin ejecutar todavía): en Aiven, `timeline_events`
#: ya existe (confirmado el 04/09/2026, con ON DELETE CASCADE) pero nunca
#: se ha corrido el Alembic de este backend contra esa base con esta
#: tabla de versiones. Antes de usar `alembic upgrade` aquí contra Aiven,
#: hace falta `alembic stamp 0002` (la cabeza real de esta cadena) —
#: nunca `upgrade`, porque `timeline_events` ya existe y `cases`/
#: `evidences` (migración 0001, bootstrap de este backend) tampoco deben
#: tocarse: las posee y las crea Casos. Ese `stamp` es una escritura
#: contra Aiven y queda pendiente de autorización explícita, igual que se
#: hizo con `alembic_version_casos` en la Fase 0 y `alembic_version_
#: tracking` en la Fase 2.
VERSION_TABLE = "alembic_version_timeline"


def _include_name(name, type_, parent_names):
    """Cortafuegos contra tocar tablas ajenas (igual que en Casos/Tracking)."""
    if type_ == "table":
        return name in TABLAS_PROPIAS
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
            include_name=_include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
