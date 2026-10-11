"""huella SHA-256 de cada copia emitida del informe

Hasta ahora, descargar un informe solo comprobaba que el fichero existiese en
el almacén. Si alguien sustituye el PDF en disco por otro documento, la API lo
sirve igual y lo presenta como el informe pericial emitido en su día: nada en
el sistema puede distinguirlos. Guardando la huella en el momento de emitirlo
y verificándola al servirlo, «este es el informe que se firmó» deja de ser una
afirmación y pasa a ser comprobable, también por quien lo recibe (la huella
viaja en la respuesta).

Una sola columna JSON con las cuatro copias, por el mismo motivo por el que
`archivo_pdf` guarda una única ruta: se emiten juntas y comparten nombre.

Es una desviación del modelo de datos oficial (CLAUDE.md) y va anotada como
tal: es la segunda columna que este módulo añade a `reports`, después de
`notas`. **No** es lo que el proyecto declara fuera de alcance — allí se
descartan los hashes *de la evidencia*, que son cadena de custodia; esto es la
huella del documento que emite este módulo.

Nullable: los informes anteriores a esta migración no la tienen y no se les
calcula, porque el hash del fichero que hoy está en disco no demuestra que sea
el que se emitió. Se sirven sin verificar.

Revision ID: m5_0004
Revises: m5_0003
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5_0004"
down_revision: Union[str, None] = "m5_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("huellas", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "huellas")
