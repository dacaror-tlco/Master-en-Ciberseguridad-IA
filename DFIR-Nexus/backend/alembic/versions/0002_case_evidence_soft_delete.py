"""cases/evidences: soft-delete + updated_at

Corrige la causa raíz del 500 en DELETE /cases/{id}: tracking_events y
reports (backends independientes sobre la misma base compartida) tienen
FKs a cases.id sin ondelete=CASCADE, así que un DELETE físico de un caso
con esos dependientes violaba integridad referencial. A partir de esta
migración, Case y Evidence solo se borran de forma lógica (columna
`eliminado` + `fecha_eliminacion`); nunca se vuelve a emitir un DELETE
físico sobre `cases` desde la aplicación.

De paso, separa fecha_actualizacion (updated_at administrativo) de
fecha_creacion/fecha_subida (alta del registro) en ambas tablas.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column(
            "fecha_actualizacion", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.add_column(
        "cases",
        sa.Column("eliminado", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("cases", sa.Column("fecha_eliminacion", sa.DateTime(), nullable=True))

    op.add_column(
        "evidences",
        sa.Column(
            "fecha_actualizacion", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.add_column(
        "evidences",
        sa.Column("eliminado", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("evidences", sa.Column("fecha_eliminacion", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidences", "fecha_eliminacion")
    op.drop_column("evidences", "eliminado")
    op.drop_column("evidences", "fecha_actualizacion")

    op.drop_column("cases", "fecha_eliminacion")
    op.drop_column("cases", "eliminado")
    op.drop_column("cases", "fecha_actualizacion")
