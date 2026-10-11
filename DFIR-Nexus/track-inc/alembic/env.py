import logging
from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import Column, Integer, Table, engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine import make_url

from alembic import context

# permite importar `app.*` al correr alembic desde la raiz del modulo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, DATABASE_URL, _connect_args_para  # noqa: E402
# Solo se registra el modelo que este backend posee (tracking_events). El
# placeholder de `cases` que existía aquí se retiró al integrar en
# `development`: el Módulo 1 es su único dueño, y un backend no debe declarar
# en su propio Alembic tablas que no posee. (La migración 0001, que crea
# `cases` y `evidences`, se conserva solo para bases locales de prueba.)
from app.modules.tracking import models as _tracking_models  # noqa: E402,F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Misma base de datos que la aplicación. Antes solo se miraba DATABASE_URL y,
# con las variables MYSQL_* del .env (el patrón del equipo), Alembic caía en la
# URL de ejemplo de alembic.ini mientras la app usaba otra base: app y
# migraciones apuntaban a sitios distintos. Si quien invoca ya fijó una URL
# real en la configuración (p. ej. un test), se respeta.
_url_ini = config.get_main_option("sqlalchemy.url")
if not _url_ini or _url_ini.startswith("driver://"):
    # configparser interpreta '%': una contraseña con caracteres escapados
    # (quote_plus -> %40...) rompía la lectura de la URL.
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

_url = config.get_main_option("sqlalchemy.url")
# Se anuncia a qué base se conecta (sin contraseña): con un .env apuntando a
# la base COMPARTIDA, conviene verlo antes de que una migración haga nada.
logging.getLogger("alembic.env").info(
    "Base de datos destino: %s", make_url(_url).render_as_string(hide_password=True)
)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# `tracking_events.case_id` es una FK a `cases.id`, tabla del Módulo 1. El
# modelo ya registra una referencia mínima (ver app/modules/tracking/models.py);
# esto es solo una red de seguridad por si faltara, porque sin ella `alembic
# check` y `revision --autogenerate` fallan con NoReferencedTableError. El
# filtro TABLAS_PROPIAS (más abajo) impide que Alembic la compare, la cree o
# la borre.
if "cases" not in target_metadata.tables:
    Table("cases", target_metadata, Column("id", Integer, primary_key=True))


# IMPORTANTE — tabla de versiones propia.
#
# La base de datos del proyecto es COMPARTIDA por todos los modulos, y cada
# uno lleva su propio historial de Alembic en su propia tabla:
#   alembic_version_casos        -> Modulo 1 (cases, evidences, ...)
#   alembic_version_scamshield   -> Modulo 2 (OSINT)
#   alembic_version_sharingan    -> Informes
#   alembic_version_tracking     -> este modulo
#
# Es el mismo nombre que usa Tracking en la rama development y el que ya
# existe en la base compartida. Si este modulo usara otra tabla (antes
# `alembic_version_trackinc`), Alembic creeria que no hay nada aplicado e
# intentaria crear tablas que ya existen.
VERSION_TABLE = "alembic_version_tracking"

# Tablas de las que este modulo es dueño. `cases` y `evidences` son del
# Modulo 1: este repositorio las declara solo como placeholder para la FK.
#
# Sin este filtro, `alembic revision --autogenerate` comparaba contra TODA la
# base de datos: al no haber modelo de `evidences`, generaba una migracion que
# la BORRABA (y lo mismo con las tablas del resto de modulos en la base
# compartida). `alembic check` lo detectaba como "remove_table evidences".
TABLAS_PROPIAS = {"tracking_events"}


def include_object(obj, name, type_, reflected, compare_to):
    """Autogenerate solo mira las tablas propias y lo que cuelga de ellas."""
    if type_ == "table":
        return name in TABLAS_PROPIAS
    tabla = getattr(obj, "table", None)
    if tabla is not None:
        return tabla.name in TABLAS_PROPIAS
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # mismos argumentos que la app: los MySQL gestionados exigen TLS
        connect_args=_connect_args_para(_url),
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
