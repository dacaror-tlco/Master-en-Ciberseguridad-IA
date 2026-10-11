"""add notas to reports

Las notas que el perito envía en POST /reports/generate entran en el prompt
y condicionan la redacción de las conclusiones. Si no quedan registradas,
el informe deja de ser reproducible: no hay forma de saber con qué
instrucciones se generó. Se persisten y se imprimen en el apartado de
antecedentes del PDF.

Revision ID: m5_0002
Revises: m5_0001
Create Date: 2026-08-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5_0002"
down_revision: Union[str, None] = "m5_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("notas", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "notas")
