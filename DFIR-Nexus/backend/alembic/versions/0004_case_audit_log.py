"""case_audit_log: rastro de auditoría único para Case y Evidence

Una sola tabla (no una por entidad) para no terminar con "Evidence audit /
Case audit" duplicando la misma información: toda fila referencia siempre
un case_id, y evidence_id solo cuando la operación fue sobre una evidencia
concreta de ese caso.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "case_id",
            sa.Integer(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_id",
            sa.Integer(),
            sa.ForeignKey("evidences.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "accion",
            sa.Enum(
                "case_creado",
                "case_actualizado",
                "case_estado_cambiado",
                "case_eliminado",
                "evidence_creada",
                "evidence_actualizada",
                "evidence_eliminada",
                name="accionauditoria",
            ),
            nullable=False,
        ),
        sa.Column("actor", sa.String(length=100), nullable=False, server_default="api"),
        sa.Column("detalle", sa.JSON(), nullable=True),
        sa.Column("creado_en", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_case_audit_log_case_id", "case_audit_log", ["case_id"])
    op.create_index("ix_case_audit_log_evidence_id", "case_audit_log", ["evidence_id"])


def downgrade() -> None:
    op.drop_index("ix_case_audit_log_evidence_id", table_name="case_audit_log")
    op.drop_index("ix_case_audit_log_case_id", table_name="case_audit_log")
    op.drop_table("case_audit_log")
    sa.Enum(name="accionauditoria").drop(op.get_bind(), checkfirst=True)
