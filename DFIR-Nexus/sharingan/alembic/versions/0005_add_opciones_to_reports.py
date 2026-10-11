"""opciones de emisión elegidas por el perito

Hasta ahora todo informe documentaba el caso entero. Un encargo acotado —solo
un día, solo los eventos graves, sin el anexo OSINT— obligaba a emitir el
informe completo y recortarlo a mano fuera del sistema, que es justo donde una
copia deja de poder contrastarse contra su original.

Con las opciones dentro del sistema, dos informes del mismo caso pueden
diferir legítimamente sin que haya cambiado ningún dato. Sin esta columna,
nada explicaría por qué: el informe declara su alcance en prosa en el apartado
1, pero esa declaración solo aparece cuando hay recorte y no se puede comparar
entre versiones. Aquí queda en un formato que sí.

Sirve además para distinguir dos cosas que la API responde distinto al pedir
un formato que no está en el almacén: «no se pidió en esta emisión» y «este
informe es anterior a que se emitieran cuatro formatos».

Tercera desviación del modelo de datos oficial (CLAUDE.md) en esta tabla,
después de `notas` y `huellas`, y como ellas pendiente de refrendo del equipo.
El criterio es el mismo que ya justificaba `notas`: lo que condiciona el
contenido del informe tiene que estar registrado, o el informe no es
reproducible.

Nullable: los informes anteriores se emitieron sin opciones, que es
exactamente lo mismo que emitirlos con las de por defecto. No hay nada que
rellenar hacia atrás.

Revision ID: m5_0005
Revises: m5_0004
Create Date: 2026-08-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5_0005"
down_revision: Union[str, None] = "m5_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("opciones", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "opciones")
