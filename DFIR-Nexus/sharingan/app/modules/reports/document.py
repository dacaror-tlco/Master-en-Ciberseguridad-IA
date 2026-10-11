"""
Contenido del informe pericial, independiente del formato de salida.

Aquí vive *qué dice* el informe; en los `*_builder.py` vive *cómo se pinta*
en cada formato. La separación no es decorativa: la estructura de un informe
pericial (UNE 197010) es la parte que un tribunal audita, y tenerla escrita
cuatro veces —una por formato— garantizaba que antes o después el PDF y el
DOCX dijeran cosas distintas bajo el mismo código de informe.

El documento se modela como una lista plana de bloques (`Titulo`, `Parrafo`,
`Tabla`, `Espacio`, `SaltoPagina`). Es deliberadamente pobre: solo contiene
las construcciones que los cuatro formatos saben representar. Cualquier
adorno que solo entienda uno de ellos es cosa de su renderizador.

Las anchuras de columna van en centímetros porque el PDF las necesita para
componer; los demás formatos las ignoran y dejan que el visor reparta.
"""
from dataclasses import dataclass, field
from datetime import datetime

from app.modules.reports.ai_narrative import Narrativa
from app.modules.reports.opciones import NOMBRE_ANEXO, Anexo, OpcionesInforme
from app.modules.reports.osint import (
    NOTA_POR_FUENTE,
    VACIO_POR_FUENTE,
    FuenteOsint,
    IndicadorOsint,
)
from app.modules.shared.models import (
    Case,
    Evidence,
    OsintResult,  # noqa: F401  (se mantiene para el tipo de `_material_analizado`)
    TimelineEvent,
    TrackingEvent,
)


@dataclass(frozen=True)
class Titulo:
    """Nivel 0 = título del documento, 1 = bloque (Anexos), 2 = sección."""

    texto: str
    nivel: int = 2


@dataclass(frozen=True)
class Parrafo:
    texto: str


@dataclass(frozen=True)
class Tabla:
    cabeceras: list[str]
    filas: list[list[str]]
    anchos_cm: list[float] | None = None


@dataclass(frozen=True)
class Espacio:
    alto_cm: float


@dataclass(frozen=True)
class SaltoPagina:
    pass


Bloque = Titulo | Parrafo | Tabla | Espacio | SaltoPagina


@dataclass(frozen=True)
class Documento:
    codigo: str
    case_id: int
    case_nombre: str
    version: int
    generado_por: str
    generado_el: datetime
    modelo_ia: str
    bloques: list[Bloque] = field(default_factory=list)

    @property
    def titulo(self) -> str:
        return f"Informe pericial {self.codigo} — {self.case_nombre}"


_METODOLOGIA = (
    "La cronología recogida en este informe no ha sido elaborada de forma manual ni "
    "estimada: procede de la tabla de eventos correlacionados del Módulo 4 (Línea Temporal) "
    "de la plataforma Nexus, que ordena de forma determinista los registros aportados por "
    "los módulos de evidencias, OSINT y tracking post-incidente. Cada evento conserva la "
    "referencia a su registro de origen, que se indica en la columna «Ref.» con el formato "
    "módulo#identificador, de modo que cualquier afirmación de este informe puede "
    "contrastarse contra el registro concreto del que procede. Todas las marcas temporales "
    "se expresan en UTC."
)

_LIMITACIONES = (
    "El alcance de este informe se limita al material listado en el apartado «Material "
    "analizado» y a los eventos recogidos en la cronología. No se han practicado "
    "diligencias adicionales fuera de ese conjunto, y las conclusiones deben interpretarse "
    "únicamente sobre esa base."
)


def codigo_informe(case_id: int, version: int) -> str:
    return f"INF-{case_id:04d}-v{version}"


def _fmt(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M UTC")


def _fmt_corto(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M")


def construir_documento(
    case: Case,
    timeline_events: list[TimelineEvent],
    narrativa: Narrativa,
    generado_por: str,
    version: int,
    generado_el: datetime,
    evidences: list[Evidence] | None = None,
    osint_results: list[IndicadorOsint] | None = None,
    fuente_osint: FuenteOsint = FuenteOsint.RESULTS,
    tracking_events: list[TrackingEvent] | None = None,
    notas: str | None = None,
    opciones: OpcionesInforme | None = None,
) -> Documento:
    evidences = evidences or []
    osint_results = osint_results or []
    tracking_events = tracking_events or []
    # Las listas llegan ya recortadas por el servicio (ver
    # `OpcionesInforme.aplicar`): aquí las opciones solo deciden qué anexos se
    # imprimen y qué declara el informe sobre su propio alcance. Filtrar en
    # dos sitios acabaría con el documento y la narrativa contando cosas
    # distintas, que es justo lo que la numeración [E1], [E2] impide.
    opciones = opciones or OpcionesInforme()
    codigo = codigo_informe(case.id, version)

    bloques: list[Bloque] = []
    _portada(bloques, case, codigo, version, generado_por, generado_el)
    _objeto_y_antecedentes(bloques, case, notas, opciones.descripcion_alcance())
    _material_analizado(bloques, evidences, osint_results, timeline_events)
    _metodologia(bloques)
    _cronologia(bloques, timeline_events)
    _hallazgos_y_conclusiones(bloques, narrativa, tracking_events)
    _declaracion_ia(bloques, narrativa)
    _firma(bloques, generado_por, generado_el)
    _anexos(
        bloques, evidences, osint_results, tracking_events, opciones.anexos, fuente_osint
    )

    return Documento(
        codigo=codigo,
        case_id=case.id,
        case_nombre=case.nombre,
        version=version,
        generado_por=generado_por,
        generado_el=generado_el,
        modelo_ia=narrativa.modelo,
        bloques=bloques,
    )


def _portada(
    bloques: list[Bloque],
    case: Case,
    codigo: str,
    version: int,
    generado_por: str,
    generado_el: datetime,
) -> None:
    bloques.append(Titulo("Informe Pericial Informático", nivel=0))
    bloques.append(Espacio(0.6))
    bloques.append(
        Tabla(
            ["Campo", "Valor"],
            [
                ["Código de informe", codigo],
                ["Versión", str(version)],
                ["Fecha de emisión", _fmt(generado_el)],
                ["Caso", f"{case.nombre} (id {case.id})"],
                ["Estado del caso", case.estado.value],
                ["Apertura del caso", _fmt(case.fecha_creacion)],
                ["Responsable del caso", case.responsable or "no asignado"],
                ["Emitido por", generado_por],
            ],
            [5, 11],
        )
    )


def _objeto_y_antecedentes(
    bloques: list[Bloque], case: Case, notas: str | None, alcance: str | None = None
) -> None:
    bloques.append(Titulo("1. Objeto y alcance"))
    bloques.append(
        Parrafo(
            f"El presente informe tiene por objeto documentar los hechos investigados en el "
            f"caso «{case.nombre}» y exponer las conclusiones periciales que de ellos se "
            f"desprenden, a partir del material analizado y de la cronología de eventos "
            f"consolidada para dicho caso."
        )
    )
    # El alcance recortado va **antes** de las limitaciones y dentro del
    # apartado 1, no en una nota al pie: quien lee el informe tiene que saber
    # qué no contiene en el mismo sitio donde se le dice qué contiene.
    if alcance:
        bloques.append(Parrafo(alcance))
    bloques.append(Parrafo(_LIMITACIONES))

    bloques.append(Titulo("2. Antecedentes"))
    bloques.append(
        Parrafo(case.descripcion)
        if case.descripcion
        else Parrafo("No consta descripción previa del caso.")
    )
    if notas:
        bloques.append(Espacio(0.2))
        bloques.append(Parrafo("Instrucciones recibidas del perito para la redacción:"))
        bloques.append(Parrafo(notas))


def _material_analizado(
    bloques: list[Bloque],
    evidences: list[Evidence],
    osint_results: list[OsintResult],
    timeline_events: list[TimelineEvent],
) -> None:
    bloques.append(Titulo("3. Material analizado"))
    bloques.append(
        Parrafo(
            f"Se han analizado {len(evidences)} evidencia(s) registrada(s) en el caso, "
            f"{len(osint_results)} consulta(s) a fuentes abiertas y "
            f"{len(timeline_events)} evento(s) de la cronología consolidada. "
            f"El detalle de las evidencias y de las consultas OSINT se recoge en los anexos."
        )
    )


def _metodologia(bloques: list[Bloque]) -> None:
    bloques.append(Titulo("4. Metodología"))
    bloques.append(Parrafo(_METODOLOGIA))


def _cronologia(bloques: list[Bloque], timeline_events: list[TimelineEvent]) -> None:
    bloques.append(Titulo("5. Cronología de eventos"))
    bloques.append(
        Tabla(
            ["Ref.", "Fecha/Hora (UTC)", "Origen", "Descripción"],
            [
                [
                    f"E{indice}",
                    _fmt_corto(event.fecha_hora),
                    f"{event.origen_modulo}#{event.origen_id}",
                    event.descripcion,
                ]
                for indice, event in enumerate(timeline_events, start=1)
            ],
            # «Origen» se ensancha a costa de la descripcion: desde que los
            # modulos usan identificadores de texto, `tracking#evt-1a4d9b30`
            # no cabe en 2,8 cm y se parte en tres lineas.
            [1.2, 2.6, 4.2, 8.0],
        )
    )


def _hallazgos_y_conclusiones(
    bloques: list[Bloque], narrativa: Narrativa, tracking_events: list[TrackingEvent]
) -> None:
    bloques.append(Titulo("6. Hallazgos"))
    _parrafos(bloques, narrativa.hallazgos)

    if tracking_events:
        bloques.append(Espacio(0.3))
        bloques.append(Parrafo("Recuento de eventos detectados por severidad:"))
        recuento = {"baja": 0, "media": 0, "alta": 0, "critica": 0}
        for event in tracking_events:
            recuento[event.severidad.value] += 1
        bloques.append(
            Tabla(
                ["Baja", "Media", "Alta", "Crítica"],
                [[str(recuento[s]) for s in ("baja", "media", "alta", "critica")]],
                [4, 4, 4, 4],
            )
        )

    bloques.append(Titulo("7. Conclusiones"))
    _parrafos(bloques, narrativa.conclusiones)


def _parrafos(bloques: list[Bloque], texto: str) -> None:
    for parrafo in texto.split("\n\n"):
        if parrafo.strip():
            bloques.append(Parrafo(parrafo.strip()))


def _declaracion_ia(bloques: list[Bloque], narrativa: Narrativa) -> None:
    bloques.append(Titulo("8. Declaración sobre el uso de inteligencia artificial"))
    bloques.append(
        Parrafo(
            f"Las secciones «Hallazgos» y «Conclusiones» de este informe han sido redactadas "
            f"con asistencia de un modelo de lenguaje ({narrativa.modelo}, nivel de esfuerzo "
            f"«{narrativa.esfuerzo}», versión de instrucciones {narrativa.version_prompt}). "
            f"El modelo se limita a redactar: no determina hechos, fechas ni severidades. "
            f"Todos los hechos proceden de la cronología correlacionada por el Módulo 4 y de "
            f"los registros referenciados en el apartado 5. Se ha verificado por procedimiento "
            f"automático que la redacción no cita ningún evento inexistente."
        )
    )
    # Solo si de verdad se archivó. Una previsualización no ha llamado a la
    # IA, y un informe no puede declarar que conserva un registro que no tiene.
    if narrativa.prompt:
        bloques.append(
            Parrafo(
                "Las instrucciones remitidas al modelo —incluida la cronología que se le "
                "facilitó— quedan archivadas literalmente junto a este informe, de modo que "
                "lo declarado en el párrafo anterior puede contrastarse con el texto que "
                "realmente se envió."
            )
        )
    bloques.append(
        Parrafo(
            "El perito firmante ha revisado el contenido de este informe y asume su "
            "responsabilidad sobre el mismo. La generación asistida no exime de dicha revisión."
        )
    )


def _firma(bloques: list[Bloque], generado_por: str, generado_el: datetime) -> None:
    bloques.append(Titulo("9. Firma"))
    bloques.append(Espacio(0.3))
    bloques.append(Parrafo(f"Emitido por: {generado_por}"))
    bloques.append(Parrafo(f"Fecha: {_fmt(generado_el)}"))
    bloques.append(Espacio(1.5))
    bloques.append(Parrafo("Firma: ______________________________"))



def _anexos(
    bloques: list[Bloque],
    evidences: list[Evidence],
    osint_results: list[IndicadorOsint],
    tracking_events: list[TrackingEvent],
    anexos: frozenset[Anexo],
    fuente_osint: FuenteOsint,
) -> None:
    """
    Imprime únicamente los anexos que esta emisión incluye.

    Un anexo excluido no deja rastro aquí —ni título, ni «no constan
    registros»—, porque decir «no constan» de algo que sí consta y no se ha
    impreso sería falso. Que falta se dice una sola vez y en su sitio: la
    declaración de alcance del apartado 1, que los nombra uno a uno.

    Los títulos salen de `NOMBRE_ANEXO`, el mismo diccionario que usa esa
    declaración: si divergieran, el lector tendría que adivinar a qué anexo
    se refiere lo que se le dice que falta.
    """
    bloques.append(SaltoPagina())
    bloques.append(Titulo("Anexos", nivel=1))

    if Anexo.EVIDENCIAS in anexos:
        _anexo_a(bloques, evidences)
    if Anexo.OSINT in anexos:
        _anexo_b(bloques, osint_results, fuente_osint)
    if Anexo.TRACKING in anexos:
        _anexo_c(bloques, tracking_events)


def _anexo_a(bloques: list[Bloque], evidences: list[Evidence]) -> None:
    bloques.append(Titulo(NOMBRE_ANEXO[Anexo.EVIDENCIAS]))
    if evidences:
        bloques.append(
            Tabla(
                ["Id", "Tipo", "Valor", "Fecha de alta (UTC)", "Observaciones"],
                [
                    [
                        str(e.id),
                        e.tipo,
                        e.valor,
                        _fmt_corto(e.fecha_subida),
                        e.observaciones or "—",
                    ]
                    for e in evidences
                ],
                [1.2, 2.4, 5.4, 2.8, 4.2],
            )
        )
    else:
        bloques.append(Parrafo("No constan evidencias registradas para este caso."))


def _anexo_b(
    bloques: list[Bloque],
    osint_results: list[IndicadorOsint],
    fuente: FuenteOsint,
) -> None:
    """
    El anexo dice de dónde ha leído los indicadores y, si no hay ninguno, por
    qué. Un anexo vacío que afirma «no constan consultas OSINT» cuando lo que
    ocurre es que su tabla no existe está afirmando algo falso sobre la
    investigación. Ver `osint.py`.
    """
    bloques.append(Titulo(NOMBRE_ANEXO[Anexo.OSINT]))
    if osint_results:
        bloques.append(
            Tabla(
                [
                    "Id",
                    "Tipo",
                    "Indicador",
                    "Reputación",
                    "País",
                    "Det.",
                    "Fuente",
                    "Consulta (UTC)",
                ],
                [
                    [
                        str(o.id),
                        o.tipo_indicador,
                        o.valor,
                        o.reputacion or "—",
                        o.pais or "—",
                        "—" if o.detecciones is None else str(o.detecciones),
                        o.fuente,
                        _fmt_corto(o.fecha_consulta),
                    ]
                    for o in osint_results
                ],
                [1.1, 1.8, 4.1, 2.0, 1.8, 1.0, 1.9, 2.3],
            )
        )
        bloques.append(Espacio(0.2))
        bloques.append(Parrafo(NOTA_POR_FUENTE[fuente]))
    else:
        bloques.append(Parrafo(VACIO_POR_FUENTE[fuente]))


def _anexo_c(bloques: list[Bloque], tracking_events: list[TrackingEvent]) -> None:
    bloques.append(Titulo(NOMBRE_ANEXO[Anexo.TRACKING]))
    if tracking_events:
        bloques.append(
            Tabla(
                ["Id", "Hora (UTC)", "Severidad", "Usuario", "Fuente de log", "Evento"],
                [
                    [
                        str(t.id),
                        _fmt_corto(t.hora),
                        t.severidad.value,
                        t.usuario_detectado or "—",
                        t.fuente_log or "—",
                        t.evento,
                    ]
                    for t in tracking_events
                ],
                [3.2, 2.4, 1.8, 2.0, 2.2, 4.4],
            )
        )
    else:
        bloques.append(
            Parrafo("No constan eventos de análisis post-incidente para este caso.")
        )
