"""
Espejo de solo lectura del esquema oficial de Nexus (ver CLAUDE.md del
proyecto: tablas `cases`, `evidences`, `osint_results`, `tracking_events` y
`timeline_events`, propiedad de los Módulos 1 a 4).

Módulo 5 nunca escribe en estas tablas. Este archivo existe únicamente
para poder desarrollar y testear el módulo de informes de forma aislada
mientras los demás módulos se construyen en sus propias ramas: define las
mismas tablas/columnas que la especificación oficial, así que cuando el
proyecto se integre en `main` basta con apuntar estos imports a los
modelos canónicos de esos módulos (mismo nombre de tabla, sin migración
de datos).

Por eso mismo: la migración Alembic de Módulo 5 (ver alembic/versions/)
NO crea estas tablas, solo `reports`. Aquí se crean aparte, solo para
desarrollo local (ver scripts/seed_dev_db.py).

`timeline_events` es la fuente de la cronología del informe. Las otras
tres tablas alimentan los anexos: el informe pericial necesita listar el
material analizado (`evidences`), los indicadores objetivos con su fecha
de consulta (`osint_results`) y la severidad de los eventos detectados
(`tracking_events`); sin eso la única prueba del informe sería la
narrativa.

**Criterio de este espejo: ser permisivo al leer.** Estas tablas las
escriben otros módulos. Dos veces ya —el `estado` del Módulo 1, la
`severidad` propuesta por el Módulo 3— un desajuste de nada habría
impedido generar *cualquier* informe. Un módulo que solo lee y solo
imprime no gana nada siendo estricto: gana no caerse. Las desviaciones
respecto al `CLAUDE.md` que eso implica van marcadas una por una.
"""
import enum
import unicodedata
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: Longitud de los identificadores ajenos. Ver `IdAjeno` más abajo.
LONGITUD_ID_AJENO = 64


def _sin_tildes(texto: str) -> str:
    """NFD separa la tilde del carácter, y luego se descarta la tilde."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def _por_texto(enum_class, value):
    """
    Busca un miembro tolerando tildes, mayúsculas y espacios sobrantes.

    El Módulo 3 propuso la severidad con tilde y el modelo de datos la
    escribe sin ella. Sin esto, esa única tilde lanza un LookupError y
    **ningún informe de ese caso se genera**. Es el mismo fallo que ya
    apareció con el `estado` del Módulo 1: coincidir en el nombre de la
    columna no basta. Y este módulo no es quién para tumbar un informe
    pericial por una tilde.

    Lo que se guarda y se imprime sigue siendo siempre el valor canónico.
    """
    if not isinstance(value, str):
        return None
    buscado = _sin_tildes(value.strip().lower())
    for miembro in enum_class:
        if _sin_tildes(miembro.value) == buscado or miembro.name.lower() == buscado:
            return miembro
    return None


class EstadoCaso(str, enum.Enum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"

    @classmethod
    def _missing_(cls, value):
        return _por_texto(cls, value)


class Severidad(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

    @classmethod
    def _missing_(cls, value):
        return _por_texto(cls, value)


class EnumTolerante(TypeDecorator):
    """
    Columna de Enum que acepta al leer cualquier variante que `_por_texto`
    sepa reconocer, y normaliza al valor canónico al escribir.

    No se usa `sa.Enum(...)` porque este módulo **no es dueño** de estas
    tablas: declarar aquí un ENUM nativo sería pretender fijar el DDL de
    otro, y además volvería a romperse ante cualquier variante ortográfica.
    """

    impl = String(30)
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return self.enum_class(value).value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum_class(value)


class IdAjeno(TypeDecorator):
    """
    Identificador de una fila que pertenece a otro módulo.

    El `CLAUDE.md` los describe como INTEGER, pero el Módulo 3 propone
    identificadores del estilo `evt-7f3a9c2e` y `obs-9f2a8b1c`. Como este
    módulo solo los **imprime** —en la columna «Ref.» de la cronología y en
    la columna «Id» de los anexos—, aceptar texto no le cuesta nada, y
    aceptar solo enteros le costaría no poder emitir el informe. Un entero
    cabe en un texto; al revés, no.

    Se normaliza a `str` al leer, para que la columna «Ref.» del informe no
    dependa de cómo devuelva el valor cada driver.

    **Desviación consciente del modelo de datos oficial**, pendiente de que
    el equipo fije el tipo definitivo. Si se acuerda INTEGER, esto sigue
    funcionando sin tocar nada.
    """

    impl = String(LONGITUD_ID_AJENO)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else str(value)


class Case(Base):
    """
    Módulo 1 — caso al que pertenece todo lo demás.

    Contrastado columna a columna contra el modelo y la migración reales de la
    rama `modulo-casos` (commit `d2fbbea`); lo comprueba
    `tests/test_esquema_modulo1.py` ejecutando el módulo contra su DDL.

    Dos diferencias deliberadas con esa tabla real, ambas del lado permisivo:

    * `estado` es aquí `String(30)` tolerante y allí un ENUM nativo. Leer un
      ENUM de MySQL como texto funciona; declarar aquí el ENUM sería fijar el
      DDL de otro módulo y volver a romperse ante cualquier variante.
    * `responsable` es aquí nullable y allí NOT NULL. Un informe no debe caerse
      por un dato de portada ausente.
    """

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    estado: Mapped[EstadoCaso] = mapped_column(EnumTolerante(EstadoCaso))
    fecha_creacion: Mapped[datetime] = mapped_column()
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable: Mapped[str | None] = mapped_column(String(100), nullable=True)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("ix_timeline_events_origen", "origen_modulo", "origen_id"),
    )

    id: Mapped[str] = mapped_column(IdAjeno, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    fecha_hora: Mapped[datetime] = mapped_column()
    descripcion: Mapped[str] = mapped_column(Text)
    origen_modulo: Mapped[str] = mapped_column(String(30))
    origen_id: Mapped[str] = mapped_column(IdAjeno)
    orden: Mapped[int] = mapped_column(Integer)


class Evidence(Base):
    """
    Módulo 1 — material objeto de análisis (anexo A del informe).

    El `ondelete="CASCADE"` está copiado de su migración real: borrar un caso
    se lleva sus evidencias. Aquí solo afecta al desarrollo local, pero que el
    espejo mienta sobre eso no ayuda a nadie.

    Ojo con la asimetría, que no es un descuido: `reports.case_id` **no**
    cascadea. Una evidencia sin caso no significa nada; un informe pericial ya
    emitido sí, y borrarlo en silencio al borrar el caso destruiría un
    documento firmado. Es el origen del 500 que hoy devuelve el Módulo 1 al
    borrar un caso con informes, y por eso lo que se le ha propuesto es un 409.
    """

    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    tipo: Mapped[str] = mapped_column(String(50))
    valor: Mapped[str] = mapped_column(Text)
    fecha_subida: Mapped[datetime] = mapped_column()
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)


class OsintResult(Base):
    """Módulo 2 — indicadores consultados en fuentes externas (anexo B)."""

    __tablename__ = "osint_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    tipo_indicador: Mapped[str] = mapped_column(String(30))
    valor: Mapped[str] = mapped_column(String(255))
    reputacion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(80), nullable=True)
    detecciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuente: Mapped[str] = mapped_column(String(50))
    fecha_consulta: Mapped[datetime] = mapped_column()
    # JSON genérico: MySQL lo materializa como JSON, SQLite (tests) como TEXT.
    # No se vuelca al PDF, solo se cita que queda almacenado en base de datos.
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class OsintFinding(Base):
    """
    Módulo 2 — capa de lectura que `scam-shield` publica para el resto de
    módulos (`osint_findings`, migración `3ea435e2a953`, 2026-09-02).

    No es la tabla del modelo de datos oficial: la especificación dice
    `osint_results` y **esa tabla no la crea nadie**, ni siquiera en la base
    compartida del equipo. El Módulo 2 mantiene ~10 tablas internas, una por
    tipo de análisis, y proyecta cada análisis terminado a esta, cuyo commit
    nombra explícitamente a informes como consumidor.

    Se lee como respaldo del Anexo B cuando `osint_results` no está. No
    sustituye a la especificación: es lo que hay mientras el equipo decide.
    Ver `repository.get_registro_osint`.

    Ojo con `case_id`: es una referencia lógica, sin clave ajena, y hoy va
    siempre a NULL. Hasta que el Módulo 2 la rellene, ningún hallazgo puede
    atribuirse a un caso, así que este respaldo no devolverá nada. Que esté
    escrito es lo que permite que funcione el día que la rellenen, sin volver
    a tocar este módulo.
    """

    __tablename__ = "osint_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    case_type: Mapped[str] = mapped_column(String(32))
    source_table: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[int] = mapped_column(Integer)
    subject_type: Mapped[str] = mapped_column(String(32))
    subject_value: Mapped[str] = mapped_column(String(255))
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(16))
    headline: Mapped[str] = mapped_column(String(255))
    flag_count: Mapped[int] = mapped_column(Integer)
    top_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column()


class TrackingEvent(Base):
    """
    Módulo 3 — eventos detectados en el análisis post-incidente (anexo C).

    Contrastado columna a columna contra el modelo y la migración reales de la
    rama `track-inc` (`6b5d49c8a514`); lo comprueba `tests/test_esquema_modulo3.py`
    ejecutando el módulo contra su DDL.

    Su tabla sigue la especificación al pie de la letra, y usa `values_callable`
    en `severidad`, así que guarda el valor (`alta`) y no el nombre de miembro
    (`ALTA`) — que es justo lo que este espejo lee.

    Hubo aquí una columna `detalles` (JSON), propuesta por el Módulo 3 en agosto
    para no perder el detalle crudo del evento. **Se retiró el 2026-09-02: su
    tabla real no la tiene.** Una columna que el espejo declara y la tabla no
    trae no es una tolerancia, es un fallo garantizado — `SELECT` la pide y
    MySQL responde «Unknown column», así que ningún informe del caso se
    generaría. El espejo refleja la tabla que existe, no la que se propuso.
    Si el Módulo 3 la añade algún día, esto se revierte y el anexo vuelve a
    citarla; la propuesta queda anotada en ESTADO.md.

    Las dos diferencias que sí se conservan son del lado permisivo, y sobre
    tipos, no sobre la existencia de la columna: `id` acepta texto además de
    enteros (`IdAjeno`) y `severidad` tolera tildes y mayúsculas
    (`EnumTolerante`). Ninguna de las dos puede romper una lectura.
    """

    __tablename__ = "tracking_events"

    id: Mapped[str] = mapped_column(IdAjeno, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    hora: Mapped[datetime] = mapped_column()
    evento: Mapped[str] = mapped_column(Text)
    severidad: Mapped[Severidad] = mapped_column(EnumTolerante(Severidad))
    fuente_log: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usuario_detectado: Mapped[str | None] = mapped_column(String(100), nullable=True)
