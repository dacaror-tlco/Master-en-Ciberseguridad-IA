"""initial: cases y evidences

Revision ID: 0001
Revises:
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("abierto", "en_progreso", "cerrado", "archivado", name="estadocaso"),
            nullable=False,
            server_default="abierto",
        ),
        sa.Column("fecha_creacion", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("responsable", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "evidences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "case_id",
            sa.Integer(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.Text(), nullable=False),
        sa.Column("fecha_subida", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
    )
    op.create_index("ix_evidences_case_id", "evidences", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_evidences_case_id", table_name="evidences")
    op.drop_table("evidences")
    op.drop_table("cases")
    sa.Enum(name="estadocaso").drop(op.get_bind(), checkfirst=True)
