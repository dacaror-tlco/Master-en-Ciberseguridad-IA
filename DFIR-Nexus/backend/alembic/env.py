from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
from app.modules.cases import models as cases_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

#: Tablas que este backend (Casos) posee. Sus migraciones solo pueden tocar
#: estas tres; ver `_include_name`. `case_audit_log` se añadió en 0004
#: (auditoría de Case/Evidence) — sigue siendo propiedad exclusiva de este
#: backend, no una tabla de otro módulo.
TABLAS_PROPIAS = frozenset({"cases", "evidences", "case_audit_log"})

#: `development` comparte una única base MySQL entre los cinco backends
#: (Casos, OSINT, Tracking, Timeline, Informes). Cada uno sella su propio
#: historial en su propia tabla de versiones para no pisarse con el Alembic
#: de otro backend apuntando a la misma base — mismo criterio que ya usan
#: OSINT (`alembic_version_scamshield`) e Informes (`alembic_version_sharingan`).
#:
#: IMPORTANTE (Fase 0, sin ejecutar todavía): en Aiven, `cases`/`evidences` ya
#: existen y la tabla `alembic_version` (la de por defecto) ya está en "0002"
#: porque Casos+Timeline se aplicaron alguna vez contra ella con el nombre de
#: tabla por defecto. Antes de que este backend vuelva a correr
#: `alembic upgrade`/`downgrade` contra Aiven con esta configuración, hace
#: falta `alembic stamp 0001` usando ya esta tabla nueva —nunca `upgrade`—,
#: para no intentar recrear `cases`/`evidences` desde cero. Ese `stamp` es una
#: escritura contra Aiven y no se ejecuta en Fase 0: queda pendiente de
#: autorización explícita.
VERSION_TABLE = "alembic_version_casos"


def _include_name(name, type_, parent_names):
    """Cortafuegos contra tocar tablas ajenas (evidences/cases son las únicas
    que este backend gestiona; ver TABLAS_PROPIAS)."""
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
