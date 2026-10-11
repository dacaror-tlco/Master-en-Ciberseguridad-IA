"""osint_findings read model

Revision ID: 3ea435e2a953
Revises: 6af9a574a7a5
Create Date: 2026-09-02 10:27:35.799937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ea435e2a953'
down_revision: Union[str, Sequence[str], None] = '6af9a574a7a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea `osint_findings`: modelo de lectura que scam-shield publica para el resto de módulos de Nexus (ver app/modules/osint/findings/models.py y docs/CONTRATO-DATOS.md)."""
    op.create_table(
        "osint_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_type", sa.String(length=32), nullable=False),
        sa.Column("source_table", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_value", sa.String(length=255), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("flag_count", sa.Integer(), nullable=False),
        sa.Column("top_flags", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_type", "source_id", name="uq_osint_finding_source"),
    )
    op.create_index(op.f("ix_osint_findings_id"), "osint_findings", ["id"], unique=False)
    op.create_index(op.f("ix_osint_findings_case_type"), "osint_findings", ["case_type"], unique=False)
    op.create_index(op.f("ix_osint_findings_source_id"), "osint_findings", ["source_id"], unique=False)
    op.create_index(op.f("ix_osint_findings_case_id"), "osint_findings", ["case_id"], unique=False)
    op.create_index(op.f("ix_osint_findings_subject_type"), "osint_findings", ["subject_type"], unique=False)
    op.create_index(op.f("ix_osint_findings_subject_value"), "osint_findings", ["subject_value"], unique=False)
    op.create_index(op.f("ix_osint_findings_risk_score"), "osint_findings", ["risk_score"], unique=False)
    op.create_index(op.f("ix_osint_findings_risk_level"), "osint_findings", ["risk_level"], unique=False)
    op.create_index(op.f("ix_osint_findings_analyzed_at"), "osint_findings", ["analyzed_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_osint_findings_analyzed_at"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_risk_level"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_risk_score"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_subject_value"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_subject_type"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_case_id"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_source_id"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_case_type"), table_name="osint_findings")
    op.drop_index(op.f("ix_osint_findings_id"), table_name="osint_findings")
    op.drop_table("osint_findings")
