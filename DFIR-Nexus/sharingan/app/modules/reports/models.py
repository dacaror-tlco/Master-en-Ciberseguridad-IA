from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        # El número de versión se calcula leyendo el máximo actual, así que dos
        # generaciones simultáneas del mismo caso pueden llegar a la misma
        # conclusión y emitir dos «v2» distintos. En un informe pericial eso
        # significa dos documentos con el mismo código INF-XXXX-vN, que es
        # exactamente lo que el código de informe existe para impedir. La base
        # de datos es el único sitio donde ese requisito se puede garantizar.
        UniqueConstraint("case_id", "version", name="uq_reports_case_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    fecha_generacion: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    resumen_ia: Mapped[str] = mapped_column(Text)
    # Ruta **relativa** a `settings.reports_storage_dir`, del estilo
    # `case_1/report_v2.pdf`. Guardarla absoluta ataba cada fila a la máquina
    # que la generó: al desplegar en Docker o mover el almacenamiento, todas
    # las filas anteriores apuntarían a ficheros inexistentes. Las filas
    # antiguas con ruta absoluta se siguen leyendo (ver service._ruta).
    archivo_pdf: Mapped[str] = mapped_column(String(255))
    generado_por: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    # Añadida sobre el modelo de datos oficial (ver CLAUDE.md) y justificada:
    # las notas del perito condicionan directamente cómo se redactan las
    # conclusiones, así que dejarlas fuera del registro rompía la
    # reproducibilidad del informe. Ver alembic/versions/0002_*.
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Huella SHA-256 de cada fichero emitido, `{"pdf": "<64 hex>", "docx": …}`:
    # las cuatro copias del informe y la transcripción del prompt («prompt»),
    # que se archiva con ellas y se le exige la misma integridad.
    # Hasta ahora la única comprobación al descargar era que el fichero
    # *existiera*: sustituirlo en disco por otro no lo detectaba nadie y se
    # seguía sirviendo como el informe auténtico. Con la huella, «este es el
    # informe que se emitió» pasa de ser una afirmación a algo demostrable,
    # que es la única versión que sirve delante de un tribunal.
    #
    # Una columna JSON en vez de cuatro columnas de texto, por el mismo
    # motivo que `archivo_pdf` guarda una sola ruta: las cuatro copias se
    # emiten juntas y se nombran igual. Añadir un formato no vuelve a tocar
    # el esquema.
    #
    # Nullable a propósito: los informes emitidos antes de esto no la tienen
    # y no se les puede calcular a posteriori sin mentir —el hash del fichero
    # que hay hoy en disco no prueba que sea el que se emitió, que es
    # justamente lo que la huella viene a demostrar—. Se siguen sirviendo,
    # sin verificar. Ver alembic/versions/0004_*.
    huellas: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    # Opciones de emisión elegidas por el perito: qué anexos entran, qué
    # franja de la cronología se documenta, qué filtros se aplicaron y en qué
    # formatos se emitió (ver opciones.py).
    #
    # Va en el registro por el mismo motivo que `notas`: sin ellas el informe
    # no es reproducible. Dos informes del mismo caso pueden diferir sin que
    # nada haya cambiado en los datos, y lo único que lo explica es esta
    # columna. El documento declara su alcance en el apartado 1, pero en
    # prosa y solo cuando hay recorte; aquí queda en un formato que se puede
    # comparar entre versiones.
    #
    # Es además lo que distingue «este formato no se pidió» de «este informe
    # es anterior a los cuatro formatos», que la API responde distinto (ver
    # service.get_report_file).
    #
    # Tercera columna que este módulo añade sobre el modelo de datos oficial,
    # después de `notas` y `huellas`, y como ellas pendiente de refrendo del
    # equipo. Nullable: los informes anteriores se emitieron sin opciones, que
    # equivale a las de por defecto.
    opciones: Mapped[dict | None] = mapped_column(JSON, nullable=True)
