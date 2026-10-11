"""auth_audit_log: nuevo valor de evento para cambio de contraseña propio

Añade "contrasena_cambiada" al ENUM `evento` de `auth_audit_log` (pantalla
de Perfil, PUT /auth/me/password). Único cambio de esquema necesario: no
se añade ninguna columna nueva.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VALORES_ANTERIORES = (
    "login_exitoso",
    "login_fallido",
    "usuario_creado",
    "usuario_desactivado",
    "usuario_reactivado",
    "rol_cambiado",
)
_VALORES_NUEVOS = _VALORES_ANTERIORES + ("contrasena_cambiada",)


def upgrade() -> None:
    op.alter_column(
        "auth_audit_log",
        "evento",
        existing_type=sa.Enum(*_VALORES_ANTERIORES, name="authevento"),
        type_=sa.Enum(*_VALORES_NUEVOS, name="authevento"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "auth_audit_log",
        "evento",
        existing_type=sa.Enum(*_VALORES_NUEVOS, name="authevento"),
        type_=sa.Enum(*_VALORES_ANTERIORES, name="authevento"),
        existing_nullable=False,
    )
