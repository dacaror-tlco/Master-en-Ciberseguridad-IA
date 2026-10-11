"""create reports table

Revision ID: m5_0001
Revises:
Create Date: 2026-08-04

Los identificadores de revisión llevan el prefijo `m5_` porque al fusionar
todos los módulos comparten un único directorio `versions/`, y el Módulo 1
(rama `modulo-casos`) ya usa el id `0001`. Dos revisiones con el mismo id
hacen que Alembic aborte con "Duplicate revision identifier", así que el
prefijo evita la colisión antes de que ocurra.

AL FUSIONAR, cambiar aquí una sola línea:

    down_revision = "0001"   # el `0001` del Módulo 1, que crea `cases`

`reports.case_id` es una FK real hacia `cases.id`, y MySQL exige que la
tabla referenciada exista antes de crear la que la referencia. Encadenar
esta revisión a la del Módulo 1 es lo que garantiza ese orden. Mientras el
módulo funcione por separado, `down_revision` tiene que seguir en None: si
apuntara al `0001` del Módulo 1 sin tener su fichero delante, Alembic no
sabría resolverlo y no arrancaría ninguna migración.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("fecha_generacion", sa.DateTime(), nullable=False),
        sa.Column("resumen_ia", sa.Text(), nullable=False),
        sa.Column("archivo_pdf", sa.String(length=255), nullable=False),
        sa.Column("generado_por", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_reports_case_id", "reports", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_case_id", table_name="reports")
    op.drop_table("reports")
