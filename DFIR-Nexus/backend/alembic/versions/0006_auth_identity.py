"""users y auth_audit_log: identidad y auditoría de acceso (Fase 1)

Dos tablas nuevas, propiedad exclusiva de este backend (Casos = autoridad
de identidad, ver propuesta de identidad y acceso):

- `users`: una única tabla de usuarios para toda la plataforma. Los demás
  backends (OSINT/Tracking/Timeline/Informes) nunca la leen ni escriben
  directamente — solo validan el JWT que ella emite.
- `auth_audit_log`: rastro de login/gestión de usuarios, deliberadamente
  separado de `case_audit_log` (un login no es un hecho sobre un caso).

Ningún módulo existente (cases/evidences/case_audit_log) se modifica.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.Enum("admin", "analyst", name="rol"), nullable=False, server_default="analyst"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("fecha_creacion", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ultimo_login", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "auth_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "evento",
            sa.Enum(
                "login_exitoso",
                "login_fallido",
                "usuario_creado",
                "usuario_desactivado",
                "usuario_reactivado",
                "rol_cambiado",
                name="authevento",
            ),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("detalle", sa.JSON(), nullable=True),
        sa.Column("creado_en", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_audit_log_user_id", "auth_audit_log", ["user_id"])
    op.create_index("ix_auth_audit_log_actor_user_id", "auth_audit_log", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_auth_audit_log_actor_user_id", table_name="auth_audit_log")
    op.drop_index("ix_auth_audit_log_user_id", table_name="auth_audit_log")
    op.drop_table("auth_audit_log")
    sa.Enum(name="authevento").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    sa.Enum(name="rol").drop(op.get_bind(), checkfirst=True)
