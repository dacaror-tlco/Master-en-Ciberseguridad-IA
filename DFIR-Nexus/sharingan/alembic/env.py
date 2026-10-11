from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Solo se importa el modelo que este módulo posee: `reports`. Las tablas
# `cases`/`timeline_events` (Módulos 1 y 4) NO se registran aquí a
# propósito, para que autogenerate nunca proponga gestionarlas desde esta
# rama (ver nota en app/modules/shared/models.py).
from app.modules.reports import models as reports_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

#: Tablas que este módulo posee y que, por tanto, sus migraciones pueden tocar.
#: Hoy solo `reports`; ver `_include_name`.
TABLAS_PROPIAS = frozenset({"reports"})

#: La base de datos de Nexus es **compartida**: los cinco módulos conviven en el
#: mismo esquema (`cases`, `evidences`, `osint_results`, `tracking_events`,
#: `timeline_events`, `reports`). Este módulo sella su historial en una tabla de
#: versiones propia y no en el `alembic_version` por defecto, para no pisarse
#: con el Alembic de otro módulo apuntando a la misma base. Mismo criterio que
#: el Módulo 2, que ya usa `alembic_version_scamshield`.
#:
#: Al fusionar en `main` esto desaparece: habrá un único historial y una única
#: tabla de versiones.
VERSION_TABLE = "alembic_version_sharingan"


def _include_name(name, type_, parent_names):
    """
    Cortafuegos contra tocar tablas ajenas.

    `env.py` importa solo el modelo de `reports`, así que hoy `Base.metadata`
    no contiene las demás. Pero eso depende de que nadie añada un import
    transitivo de `app.modules.shared.models` —el espejo de solo lectura—, y si
    alguien lo hiciera, un `--autogenerate` contra la base compartida propondría
    **modificar las tablas de otros módulos** para que se parezcan al espejo:
    convertir `tracking_events.id` en VARCHAR, crear `osint_results`, quitar
    claves ajenas. Es decir, escribiría migraciones destructivas sobre datos que
    no son de este módulo.

    Con esto, la lista de lo que Alembic puede gestionar desde aquí es
    explícita y no depende del grafo de imports.
    """
    if type_ == "table":
        return name in TABLAS_PROPIAS
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
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
