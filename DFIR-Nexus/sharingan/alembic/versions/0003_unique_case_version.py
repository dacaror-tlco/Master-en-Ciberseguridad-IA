"""restriccion unica sobre (case_id, version) en reports

El número de versión se obtiene leyendo el máximo actual y sumando uno, así
que dos generaciones simultáneas del mismo caso pueden calcular el mismo y
emitir dos «v2» distintos. Eso produce dos documentos periciales diferentes
bajo el mismo código INF-XXXX-vN, que es justo lo que ese código existe para
impedir. El reintento en el servicio resuelve la colisión, pero solo puede
detectarla si la base de datos la rechaza.

No añade columnas: no toca el modelo de datos oficial del proyecto.

Revision ID: m5_0003
Revises: m5_0002
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "m5_0003"
down_revision: Union[str, None] = "m5_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # En modo por lotes porque SQLite no sabe añadir restricciones a una tabla
    # existente (`ALTER TABLE ADD CONSTRAINT` no existe allí): Alembic recrea la
    # tabla y copia los datos. En MySQL, que es el destino real, se traduce a un
    # ALTER normal. Sin esto la migración solo corría en MySQL, y el entorno de
    # desarrollo con SQLite se quedaba sin poder aplicarla.
    with op.batch_alter_table("reports") as lote:
        lote.create_unique_constraint("uq_reports_case_version", ["case_id", "version"])


def downgrade() -> None:
    with op.batch_alter_table("reports") as lote:
        lote.drop_constraint("uq_reports_case_version", type_="unique")
