"""add composite index (origen_modulo, origen_id) on timeline_events

Revisión corregida (auditoría Módulo 4, 2026-09-27): la versión original
creaba el índice a ciegas. La migración 0002 ya lo crea también, así que
un `alembic upgrade head` sobre una base limpia fallaba con
"Duplicate key name 'ix_timeline_events_origen'". Ahora esta migración
comprueba si el índice ya existe y solo lo crea si no está — es segura
tanto en bases limpias (donde 0002 ya lo creó) como en Aiven (donde el
índice existe y esta revisión está estampada).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def _index_exists(index_name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return index_name in {ix["name"] for ix in insp.get_indexes("timeline_events")}


def upgrade() -> None:
    if not _index_exists("ix_timeline_events_origen"):
        op.create_index(
            "ix_timeline_events_origen",
            "timeline_events",
            ["origen_modulo", "origen_id"],
        )


def downgrade() -> None:
    if _index_exists("ix_timeline_events_origen"):
        op.drop_index("ix_timeline_events_origen", table_name="timeline_events")
