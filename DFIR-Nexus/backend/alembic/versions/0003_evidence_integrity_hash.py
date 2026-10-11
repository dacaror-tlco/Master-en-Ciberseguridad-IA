"""evidences: hash_valor (integridad) + fecha_adquisicion (timestamp forense)

hash_valor es la huella SHA-256 del contenido probatorio (`valor`),
calculada una única vez. Como las filas existentes no tienen huella, la
columna se añade primero como NULLABLE, se rellena con el hash real de
cada `valor` existente y solo entonces se aprieta a NOT NULL — así ninguna
fila queda con un hash inventado ni la migración falla contra datos ya
presentes en Aiven.

fecha_adquisicion es nullable sin más: para evidencias ya existentes no se
conoce (ni se inventa) el momento real de adquisición; solo fecha_subida
(alta del registro) sigue siendo fiable para ellas.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-10

"""
import hashlib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


evidences_tabla = sa.table(
    "evidences",
    sa.column("id", sa.Integer),
    sa.column("valor", sa.Text),
    sa.column("hash_valor", sa.String),
)


def upgrade() -> None:
    op.add_column("evidences", sa.Column("fecha_adquisicion", sa.DateTime(), nullable=True))
    op.add_column("evidences", sa.Column("hash_valor", sa.String(length=64), nullable=True))

    conexion = op.get_bind()
    filas = conexion.execute(sa.select(evidences_tabla.c.id, evidences_tabla.c.valor)).fetchall()
    for fila_id, valor in filas:
        hash_valor = hashlib.sha256((valor or "").encode("utf-8")).hexdigest()
        conexion.execute(
            evidences_tabla.update()
            .where(evidences_tabla.c.id == fila_id)
            .values(hash_valor=hash_valor)
        )

    op.alter_column("evidences", "hash_valor", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    op.drop_column("evidences", "hash_valor")
    op.drop_column("evidences", "fecha_adquisicion")
