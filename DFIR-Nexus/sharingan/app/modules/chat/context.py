"""
Cómo se le da al modelo lo que sabe del caso.

Mismo principio que el resto del Módulo 5 (ver `ai_narrative.py`): **el LLM
no decide hechos**. Aquí no decide ni siquiera qué mirar — el contexto se
arma por código, con las mismas consultas deterministas que usa el informe
(`reports/repository.py`), y el modelo solo redacta sobre lo que se le pone
delante. No tiene acceso a la base de datos, ni herramientas, ni forma de
consultar otro caso: si algo no está en este texto, para él no existe.

Cada fila entra numerada con una referencia estable (`EV3`, `TR7`, `TL2`…)
y al modelo se le exige citarla. Después, `service.py` comprueba por código
que no ha citado ninguna que no se le pasara. Es la misma comprobación de
alucinación barata que ya hace el informe, y por el mismo motivo: en un
contexto pericial, una afirmación que no se puede rastrear hasta una fila
concreta no vale nada.

**Recorte declarado, nunca silencioso.** Un caso con miles de eventos no
cabe en una ventana de contexto. Se recorta por tanto cada colección a un
tope, pero el recorte se le dice al modelo *y* se devuelve al frontend, que
lo pinta. Es la misma regla que el alcance de emisión del informe
(`opciones.py`): omitir sin decirlo convierte un «no consta» en una
afirmación falsa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.modules.reports import repository as reports_repo
from app.modules.reports.osint import FuenteOsint, RegistroOsint
from app.modules.shared.models import Case

#: Filas como máximo por colección. Números elegidos para que un caso grande
#: siga cabiendo holgadamente junto con el historial de conversación.
TOPES: dict[str, int] = {
    "evidences": 100,
    "osint": 100,
    "tracking_events": 200,
    "timeline_events": 300,
    "reports": 25,
}


@dataclass(frozen=True)
class Fuente:
    """Una fila real de la base, con la referencia con la que se cita."""

    ref: str
    tabla: str
    fila_id: str
    resumen: str
    #: Línea tal cual se le pasa al modelo. Más detallada que `resumen`, que
    #: es lo que se pinta en la interfaz.
    linea: str


@dataclass
class ContextoCaso:
    case: Case
    fuentes: list[Fuente] = field(default_factory=list)
    #: Avisos de recorte y de disponibilidad de registros, en el mismo texto
    #: que se le da al modelo y que se devuelve al frontend.
    avisos: list[str] = field(default_factory=list)

    @property
    def refs(self) -> set[str]:
        return {f.ref for f in self.fuentes}


def _recortar(filas: list, clave: str, etiqueta: str, avisos: list[str]) -> list:
    tope = TOPES[clave]
    if len(filas) <= tope:
        return filas
    avisos.append(
        f"{etiqueta}: se muestran {tope} de {len(filas)} registros "
        f"(los más antiguos). El asistente no ha visto el resto."
    )
    return filas[:tope]


def construir(db: Session, case_id: int) -> ContextoCaso | None:
    """
    Reúne todo lo que consta del caso en las seis tablas del contrato.

    Devuelve `None` si el caso no existe — deliberadamente distinto de un caso
    que existe y está vacío, que sí devuelve un contexto con cero fuentes: al
    perito hay que decirle «ese caso no existe», no «no consta nada».
    """
    case = reports_repo.get_case(db, case_id)
    if case is None:
        return None
    return armar(
        case,
        evidencias=reports_repo.get_evidences(db, case_id),
        registro=reports_repo.get_registro_osint(db, case_id),
        tracking=reports_repo.get_tracking_events(db, case_id),
        cronologia=reports_repo.get_timeline_events(db, case_id),
        informes=reports_repo.list_reports_for_case(db, case_id),
    )


def armar(
    case,
    *,
    evidencias: list,
    registro: RegistroOsint,
    tracking: list,
    cronologia: list,
    informes: list,
    avisos: list[str] | None = None,
) -> ContextoCaso:
    """
    Numera las filas y las convierte en líneas citables.

    Separado de la lectura a propósito: el contexto se puede leer de la base
    (`construir`) o a través del servidor MCP (`fuente_mcp.construir`), y lo
    que ve el modelo —numeración, formato, recortes declarados— tiene que ser
    el mismo en los dos casos, o las citas dejarían de significar lo mismo.
    Recibe objetos con los atributos de los modelos ORM, vengan de donde vengan.
    """
    ctx = ContextoCaso(case=case, avisos=list(avisos or []))

    evidencias = _recortar(evidencias, "evidences", "Evidencias", ctx.avisos)
    for n, ev in enumerate(evidencias, start=1):
        obs = f" — {ev.observaciones}" if ev.observaciones else ""
        ctx.fuentes.append(
            Fuente(
                ref=f"EV{n}",
                tabla="evidences",
                fila_id=str(ev.id),
                resumen=f"{ev.tipo}: {ev.valor}",
                linea=(
                    f"[EV{n}] evidencia #{ev.id} · {ev.fecha_subida.isoformat()} · "
                    f"tipo={ev.tipo} · valor={ev.valor}{obs}"
                ),
            )
        )

    if registro.fuente is FuenteOsint.NO_DISPONIBLE:
        ctx.avisos.append(
            "OSINT: el registro de indicadores no está disponible en esta base de "
            "datos. No significa que no se hicieran consultas, sino que el "
            "asistente no ha podido leerlas."
        )
    elif registro.fuente is FuenteOsint.FINDINGS:
        ctx.avisos.append(
            "OSINT: los indicadores proceden del registro consolidado del Módulo 2 "
            "(osint_findings), no de osint_results. La reputación es la "
            "clasificación de riesgo de ese módulo, no el veredicto de la fuente "
            "externa."
        )
    indicadores = _recortar(registro.indicadores, "osint", "OSINT", ctx.avisos)
    for n, ind in enumerate(indicadores, start=1):
        ctx.fuentes.append(
            Fuente(
                ref=f"OS{n}",
                tabla=registro.fuente.value,
                fila_id=ind.id,
                resumen=f"{ind.tipo_indicador}: {ind.valor}",
                linea=(
                    f"[OS{n}] indicador #{ind.id} · {ind.fecha_consulta.isoformat()} · "
                    f"tipo={ind.tipo_indicador} · valor={ind.valor} · "
                    f"reputación={ind.reputacion or 'no consta'} · "
                    f"país={ind.pais or 'no consta'} · "
                    f"detecciones={ind.detecciones if ind.detecciones is not None else 'no consta'} · "
                    f"fuente={ind.fuente}"
                ),
            )
        )

    tracking = _recortar(tracking, "tracking_events", "Tracking", ctx.avisos)
    for n, tr in enumerate(tracking, start=1):
        ctx.fuentes.append(
            Fuente(
                ref=f"TR{n}",
                tabla="tracking_events",
                fila_id=str(tr.id),
                resumen=f"[{tr.severidad.value}] {tr.evento}",
                linea=(
                    f"[TR{n}] evento #{tr.id} · {tr.hora.isoformat()} · "
                    f"severidad={tr.severidad.value} · "
                    f"usuario={tr.usuario_detectado or 'no consta'} · "
                    f"log={tr.fuente_log or 'no consta'} · {tr.evento}"
                ),
            )
        )

    cronologia = _recortar(cronologia, "timeline_events", "Cronología", ctx.avisos)
    for n, tl in enumerate(cronologia, start=1):
        ctx.fuentes.append(
            Fuente(
                ref=f"TL{n}",
                tabla="timeline_events",
                fila_id=str(tl.id),
                resumen=tl.descripcion,
                linea=(
                    f"[TL{n}] cronología #{tl.id} · {tl.fecha_hora.isoformat()} · "
                    f"origen={tl.origen_modulo}#{tl.origen_id} · {tl.descripcion}"
                ),
            )
        )

    informes = _recortar(informes, "reports", "Informes", ctx.avisos)
    for n, rep in enumerate(informes, start=1):
        ctx.fuentes.append(
            Fuente(
                ref=f"IN{n}",
                tabla="reports",
                fila_id=str(rep.id),
                resumen=f"Informe v{rep.version} ({rep.fecha_generacion:%Y-%m-%d})",
                linea=(
                    f"[IN{n}] informe #{rep.id} · v{rep.version} · "
                    f"{rep.fecha_generacion.isoformat()} · "
                    f"generado por {rep.generado_por or 'no consta'}"
                ),
            )
        )

    return ctx


def a_texto(ctx: ContextoCaso) -> str:
    """El bloque de contexto tal cual viaja en el prompt de usuario."""
    lineas = [
        "=== EXPEDIENTE DEL CASO ===",
        f"Caso #{ctx.case.id}: {ctx.case.nombre}",
        f"Estado: {ctx.case.estado.value}",
        f"Responsable: {ctx.case.responsable or 'no asignado'}",
        f"Fecha de creación: {ctx.case.fecha_creacion.isoformat()}",
    ]
    if ctx.case.descripcion:
        lineas.append(f"Descripción: {ctx.case.descripcion}")

    if ctx.avisos:
        lineas.append("")
        lineas.append("Limitaciones de este contexto (comunícaselas al perito si "
                      "afectan a la respuesta):")
        lineas.extend(f"- {a}" for a in ctx.avisos)

    lineas.append("")
    if ctx.fuentes:
        lineas.append("Registros del caso (cita la referencia entre corchetes):")
        lineas.extend(f.linea for f in ctx.fuentes)
    else:
        lineas.append(
            "No consta ningún registro asociado a este caso: ni evidencias, ni "
            "indicadores OSINT, ni eventos de tracking, ni cronología, ni informes."
        )

    return "\n".join(lineas)
