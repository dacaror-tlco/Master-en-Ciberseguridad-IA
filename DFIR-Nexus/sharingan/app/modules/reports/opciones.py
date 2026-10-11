"""
Opciones de emisión del informe: qué anexos entran, qué franja de la
cronología se documenta y en qué soportes se emite.

El perito no siempre quiere el caso entero. Un informe puede pedirse acotado
a un día concreto, o solo sobre los eventos graves, o sin el anexo OSINT
porque el encargo no lo cubre. Antes eso obligaba a emitir el informe completo
y recortarlo a mano fuera del sistema, que es exactamente donde una copia deja
de poder contrastarse contra su original.

**Las dos reglas que gobiernan este módulo, y de las que sale todo lo demás:**

1. *Nada se omite en silencio.* Si esta emisión deja fuera un anexo o una
   franja temporal, el propio documento lo dice en su apartado 1 (ver
   `descripcion_alcance`). Un informe recortado sin declararlo es un informe
   que engaña sobre su propio alcance, y eso lo lee un juez.

2. *La columna «Ref.» siempre resuelve.* La metodología del informe promete
   que cualquier afirmación puede contrastarse contra el registro del que
   procede. Por eso un filtro nunca puede dejar en la cronología una entrada
   que apunte a una fila que el informe no imprime: al descartar una fila se
   descartan también las entradas de cronología que la referencian. Así el
   invariante se cumple por construcción y no por vigilancia
   (`tests/test_contrato_modulos.py::test_cada_referencia_de_la_cronologia_
   resuelve_en_los_anexos`).

Sin opciones, `OpcionesInforme()` reproduce exactamente el informe de siempre:
todos los anexos, toda la cronología, los cuatro formatos y ningún párrafo de
alcance añadido. Es deliberado — la personalización no debía cambiar lo que ya
se emitía.

`FormatoInforme` vive aquí, y no en `formats.py` como antes, porque es
vocabulario de una opción: qué soportes se emiten. `formats.py` lo reexporta,
así que quien lo importaba de allí lo sigue encontrando.
"""
import enum
from dataclasses import dataclass, field
from datetime import datetime

from app.modules.reports.osint import IndicadorOsint
from app.modules.shared.models import (
    Evidence,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)


class FormatoInforme(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    JSON = "json"


class Anexo(str, enum.Enum):
    """
    Los tres anexos, identificados por el valor que `timeline_events.
    origen_modulo` usa para apuntar a ellos.

    Que el valor coincida con el de `origen_modulo` no es cosmético: es la
    clave con la que se cruza una entrada de cronología con el anexo que la
    respalda, y por tanto lo que hace comprobable la regla 2 de arriba.
    """

    EVIDENCIAS = "evidences"  # Anexo A
    OSINT = "osint"  # Anexo B
    TRACKING = "tracking"  # Anexo C


#: Título con el que cada anexo aparece en el informe, para poder nombrarlos
#: en la declaración de alcance tal y como los ve quien lo lee.
NOMBRE_ANEXO: dict[Anexo, str] = {
    Anexo.EVIDENCIAS: "Anexo A — Inventario de evidencias",
    Anexo.OSINT: "Anexo B — Indicadores consultados en fuentes abiertas",
    Anexo.TRACKING: "Anexo C — Eventos de análisis post-incidente",
}

#: De menor a mayor. `Severidad` es un Enum de cadenas y no se puede ordenar
#: solo, así que el orden pericial se declara aquí en vez de deducirse del
#: alfabeto —donde «alta» iría antes que «baja»—.
_ORDEN_SEVERIDAD: list[Severidad] = [
    Severidad.BAJA,
    Severidad.MEDIA,
    Severidad.ALTA,
    Severidad.CRITICA,
]

TODOS_LOS_ANEXOS: frozenset[Anexo] = frozenset(Anexo)
TODOS_LOS_FORMATOS: frozenset[FormatoInforme] = frozenset(FormatoInforme)


@dataclass(frozen=True)
class Seleccion:
    """El material que finalmente entra en el informe, ya filtrado."""

    timeline_events: list[TimelineEvent]
    evidences: list[Evidence]
    osint_results: list[IndicadorOsint]
    tracking_events: list[TrackingEvent]


@dataclass(frozen=True)
class OpcionesInforme:
    anexos: frozenset[Anexo] = field(default=TODOS_LOS_ANEXOS)
    formatos: frozenset[FormatoInforme] = field(default=TODOS_LOS_FORMATOS)
    desde: datetime | None = None
    hasta: datetime | None = None
    severidad_minima: Severidad | None = None
    solo_osint_con_detecciones: bool = False

    def __post_init__(self) -> None:
        if not self.anexos:
            # Sin ningún anexo no queda nada que respalde la cronología, así
            # que toda entrada se quedaría sin referencia imprimible y el
            # informe no tendría cronología. Es el mismo motivo por el que un
            # caso sin `timeline_events` devuelve 422.
            raise ValueError(
                "Hay que incluir al menos un anexo: un informe sin ninguno no "
                "puede respaldar ninguna entrada de la cronología."
            )
        if FormatoInforme.PDF not in self.formatos:
            # El PDF es el documento que se firma y el que registra
            # `reports.archivo_pdf`. Los demás son copias suyas en otros
            # soportes; emitir copias sin original no significa nada.
            raise ValueError(
                "El PDF no se puede excluir: es el documento que se firma y al "
                "que se refieren las demás copias."
            )
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError(
                "La franja temporal está invertida: «desde» es posterior a «hasta»."
            )

    @property
    def hay_recorte(self) -> bool:
        """
        Si esta emisión deja fuera algo que por defecto entraría.

        Gobierna dos cosas: que los anexos se reduzcan a lo que la cronología
        respalda (ver `aplicar`) y que el informe declare su alcance (ver
        `descripcion_alcance`). Los formatos no cuentan: no recortan el
        contenido del documento, solo en cuántos soportes se emite.
        """
        return (
            self.anexos != TODOS_LOS_ANEXOS
            or self.desde is not None
            or self.hasta is not None
            or self.severidad_minima is not None
            or self.solo_osint_con_detecciones
        )

    def aplicar(
        self,
        timeline_events: list[TimelineEvent],
        evidences: list[Evidence],
        osint_results: list[IndicadorOsint],
        tracking_events: list[TrackingEvent],
    ) -> Seleccion:
        """
        Recorta el material del caso a lo que esta emisión documenta.

        El orden importa y es el que garantiza la regla 2:

        1. Se filtran las filas de cada anexo por sus propios criterios.
        2. Se filtra la cronología por la franja temporal **y** se descarta
           toda entrada cuya fila de origen no haya sobrevivido al paso 1.
        3. Si hay recorte, cada anexo se reduce a las filas que la cronología
           resultante referencia. Así el informe no arrastra material que ya
           no respalda nada de lo que cuenta.

        Una entrada de cronología cuyo `origen_id` no corresponde a ninguna
        fila del caso —dato inconsistente de otro módulo— se conserva, que es
        lo que ya hacía antes: recortar es cosa de las opciones, no la ocasión
        de empezar a descartar datos ajenos por nuestra cuenta.
        """
        evidencias_sel = [
            e for e in evidences if Anexo.EVIDENCIAS in self.anexos
        ]
        osint_sel = [
            o
            for o in osint_results
            if Anexo.OSINT in self.anexos
            and (not self.solo_osint_con_detecciones or (o.detecciones or 0) > 0)
        ]
        tracking_sel = [
            t
            for t in tracking_events
            if Anexo.TRACKING in self.anexos and self._pasa_severidad(t)
        ]

        supervivientes: dict[str, set[str]] = {
            Anexo.EVIDENCIAS.value: {str(e.id) for e in evidencias_sel},
            Anexo.OSINT.value: {str(o.id) for o in osint_sel},
            Anexo.TRACKING.value: {str(t.id) for t in tracking_sel},
        }
        conocidos: dict[str, set[str]] = {
            Anexo.EVIDENCIAS.value: {str(e.id) for e in evidences},
            Anexo.OSINT.value: {str(o.id) for o in osint_results},
            Anexo.TRACKING.value: {str(t.id) for t in tracking_events},
        }

        cronologia = [
            evento
            for evento in timeline_events
            if self._en_franja(evento.fecha_hora)
            and self._origen_sobrevive(evento, supervivientes, conocidos)
        ]

        if not self.hay_recorte:
            return Seleccion(cronologia, evidencias_sel, osint_sel, tracking_sel)

        referenciados = {clave: set() for clave in supervivientes}
        for evento in cronologia:
            destino = referenciados.get(str(evento.origen_modulo))
            if destino is not None:
                destino.add(str(evento.origen_id))

        return Seleccion(
            timeline_events=cronologia,
            evidences=[
                e
                for e in evidencias_sel
                if str(e.id) in referenciados[Anexo.EVIDENCIAS.value]
            ],
            osint_results=[
                o for o in osint_sel if str(o.id) in referenciados[Anexo.OSINT.value]
            ],
            tracking_events=[
                t
                for t in tracking_sel
                if str(t.id) in referenciados[Anexo.TRACKING.value]
            ],
        )

    def _pasa_severidad(self, evento: TrackingEvent) -> bool:
        if self.severidad_minima is None:
            return True
        return _ORDEN_SEVERIDAD.index(evento.severidad) >= _ORDEN_SEVERIDAD.index(
            self.severidad_minima
        )

    def _en_franja(self, momento: datetime) -> bool:
        # Las fechas del almacén llegan sin zona (MySQL DATETIME) y las que
        # entran por la API pueden traerla. Comparar unas con otras revienta,
        # así que se comparan ambas como UTC ingenuo, que es lo que el resto
        # del módulo ya asume al imprimir «(UTC)».
        instante = _sin_zona(momento)
        if self.desde and instante < _sin_zona(self.desde):
            return False
        if self.hasta and instante > _sin_zona(self.hasta):
            return False
        return True

    @staticmethod
    def _origen_sobrevive(
        evento: TimelineEvent,
        supervivientes: dict[str, set[str]],
        conocidos: dict[str, set[str]],
    ) -> bool:
        modulo = str(evento.origen_modulo)
        if modulo not in conocidos:
            # `origen_modulo` no nombra ninguno de los tres anexos. El módulo
            # ya rechaza esto al validar el contrato con los otros módulos;
            # aquí no es sitio para decidirlo, así que se deja pasar.
            return True
        origen = str(evento.origen_id)
        if origen not in conocidos[modulo]:
            return True  # Referencia colgante en los datos de origen.
        return origen in supervivientes[modulo]

    def descripcion_alcance(self) -> str | None:
        """
        El párrafo que el informe añade a su apartado 1 cuando esta emisión
        no cubre el caso entero. `None` si no hay nada que declarar.

        Se redacta aquí, y no en el prompt, porque no es narrativa: es un
        hecho sobre la emisión y no puede quedar a criterio del modelo.
        """
        if not self.hay_recorte:
            return None

        partes: list[str] = []
        if self.desde or self.hasta:
            if self.desde and self.hasta:
                franja = (
                    f"a los hechos comprendidos entre el {_fecha(self.desde)} y el "
                    f"{_fecha(self.hasta)} (UTC)"
                )
            elif self.desde:
                franja = f"a los hechos posteriores al {_fecha(self.desde)} (UTC)"
            else:
                franja = f"a los hechos anteriores al {_fecha(self.hasta)} (UTC)"
            partes.append(franja)
        if self.severidad_minima:
            partes.append(
                f"a los eventos de severidad {self.severidad_minima.value} o superior"
            )
        if self.solo_osint_con_detecciones:
            partes.append("a los indicadores OSINT con detecciones registradas")

        excluidos = sorted(
            NOMBRE_ANEXO[anexo] for anexo in TODOS_LOS_ANEXOS - self.anexos
        )

        texto = (
            "Alcance de esta emisión: a petición del perito, el presente informe no "
            "documenta el caso en su totalidad."
        )
        if partes:
            texto += " Se ha limitado " + "; ".join(partes) + "."
        if excluidos:
            texto += (
                " Se han excluido los siguientes anexos y, con ellos, las entradas de "
                "la cronología que se apoyaban en ellos: " + "; ".join(excluidos) + "."
            )
        texto += (
            " Los anexos recogen únicamente el material que respalda la cronología aquí "
            "documentada. El caso puede contener registros adicionales fuera de este "
            "alcance, consultables en el sistema del que procede este informe."
        )
        return texto

    def como_json(self) -> dict:
        """Lo que se guarda en `reports.opciones`. Ver el modelo."""
        return {
            "anexos": sorted(anexo.value for anexo in self.anexos),
            "formatos": sorted(formato.value for formato in self.formatos),
            "desde": self.desde.isoformat() if self.desde else None,
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "severidad_minima": (
                self.severidad_minima.value if self.severidad_minima else None
            ),
            "solo_osint_con_detecciones": self.solo_osint_con_detecciones,
        }


def _sin_zona(momento: datetime) -> datetime:
    return momento.replace(tzinfo=None) if momento.tzinfo else momento


def _fecha(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M")
