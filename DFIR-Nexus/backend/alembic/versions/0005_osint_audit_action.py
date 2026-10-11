"""case_audit_log: nuevo valor de accion para vinculaciones OSINT

Añade "osint_vinculacion_cambiada" al ENUM `accion` de `case_audit_log`.
Es el único cambio de esquema necesario para registrar los cambios de
vinculación de una investigación OSINT con un caso (NULL->caso,
caso->otro caso, caso->NULL): el detalle de cada cambio (case_type,
source_id, caso anterior, caso nuevo) va en la columna `detalle` (JSON)
que ya existe, sin añadir ninguna columna nueva.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VALORES_ANTERIORES = (
    "case_creado",
    "case_actualizado",
    "case_estado_cambiado",
    "case_eliminado",
    "evidence_creada",
    "evidence_actualizada",
    "evidence_eliminada",
)
_VALORES_NUEVOS = _VALORES_ANTERIORES + ("osint_vinculacion_cambiada",)


def upgrade() -> None:
    op.alter_column(
        "case_audit_log",
        "accion",
        existing_type=sa.Enum(*_VALORES_ANTERIORES, name="accionauditoria"),
        type_=sa.Enum(*_VALORES_NUEVOS, name="accionauditoria"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "case_audit_log",
        "accion",
        existing_type=sa.Enum(*_VALORES_NUEVOS, name="accionauditoria"),
        type_=sa.Enum(*_VALORES_ANTERIORES, name="accionauditoria"),
        existing_nullable=False,
    )
