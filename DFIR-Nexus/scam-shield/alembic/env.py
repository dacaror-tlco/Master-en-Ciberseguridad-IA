from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
from app.modules.osint.cnmv import models as cnmv_models  # noqa: F401
from app.modules.osint.domain import models as domain_models  # noqa: F401
from app.modules.osint.email import models as email_models  # noqa: F401
from app.modules.osint.findings import models as findings_models  # noqa: F401
from app.modules.osint.image import models as image_models  # noqa: F401
from app.modules.osint.integrity import models as integrity_models  # noqa: F401
from app.modules.osint.ip import models as ip_models  # noqa: F401
from app.modules.osint.monitoring import models as monitoring_models  # noqa: F401
from app.modules.osint.phone import models as phone_models  # noqa: F401
from app.modules.osint.typosquatting import models as typosquatting_models  # noqa: F401
from app.modules.osint.wallet import models as wallet_models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# La base de datos de Nexus es COMPARTIDA: scam-shield convive en el mismo
# esquema con las tablas de otros módulos (cases, evidences, timeline_events,
# tracking_events, reports...). Dos defensas:
#
# 1. version_table propia: scam-shield sella su historial de migraciones en
#    `alembic_version_scamshield`, no en el `alembic_version` por defecto, para
#    no pisarse con el Alembic de otro módulo apuntando a la misma base.
# 2. include_name: autogenerate solo mira las tablas que scam-shield declara en
#    su metadata; así nunca genera un `drop_table` de una tabla de otro módulo.
_VERSION_TABLE = "alembic_version_scamshield"


def _include_name(name, type_, parent_names):
    if type_ == "table":
        return name in target_metadata.tables
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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=_VERSION_TABLE,
        include_name=_include_name,
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
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=_VERSION_TABLE,
            include_name=_include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
