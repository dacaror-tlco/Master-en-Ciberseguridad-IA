from datetime import datetime

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.modules.reports.models import Report
from app.modules.reports.osint import (
    FuenteOsint,
    RegistroOsint,
    desde_osint_finding,
    desde_osint_result,
)
from app.modules.shared.models import (
    Case,
    Evidence,
    OsintFinding,
    OsintResult,
    TimelineEvent,
    TrackingEvent,
)


def get_case(db: Session, case_id: int) -> Case | None:
    return db.get(Case, case_id)


def get_timeline_events(db: Session, case_id: int) -> list[TimelineEvent]:
    stmt = (
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        # El apartado de metodología del informe afirma que la cronología está
        # ordenada de forma determinista. `orden` no es único —lo fija el
        # Módulo 4—, así que sin desempate dos eventos con el mismo valor
        # saldrían en el orden que decidiese la base de datos, y dos versiones
        # del mismo informe podrían contradecirse.
        .order_by(TimelineEvent.orden, TimelineEvent.fecha_hora, TimelineEvent.id)
    )
    return list(db.scalars(stmt))


def get_evidences(db: Session, case_id: int) -> list[Evidence]:
    stmt = (
        select(Evidence)
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.fecha_subida, Evidence.id)
    )
    return list(db.scalars(stmt))


def get_registro_osint(db: Session, case_id: int) -> RegistroOsint:
    """
    Los indicadores OSINT del caso, y de qué tabla se han podido leer.

    Se comprueba que la tabla exista **antes** de consultarla, en vez de
    intentarlo y recoger el error. Dos motivos: el mensaje varía según el
    motor —«no such table» en SQLite, «Table ... doesn't exist» en MySQL—, y
    sobre todo un `SELECT` fallido dentro de una transacción la deja
    inutilizable, así que recoger el error obligaría a un `rollback` a mitad de
    componer el informe.

    Preferencia: `osint_results` (el registro del modelo de datos oficial) y,
    si no existe, `osint_findings` (la capa de lectura del Módulo 2). Nunca las
    dos: mezclar dos registros con vocabularios distintos en una sola tabla
    daría un anexo que no se puede leer sin saber de dónde viene cada fila.

    Ver `osint.py` para qué declara el informe en cada caso.
    """
    inspector = inspect(db.get_bind())

    if inspector.has_table(OsintResult.__tablename__):
        filas = db.scalars(
            select(OsintResult)
            .where(OsintResult.case_id == case_id)
            .order_by(OsintResult.fecha_consulta, OsintResult.id)
        )
        return RegistroOsint(
            [desde_osint_result(f) for f in filas], FuenteOsint.RESULTS
        )

    if inspector.has_table(OsintFinding.__tablename__):
        filas = db.scalars(
            select(OsintFinding)
            .where(OsintFinding.case_id == case_id)
            .order_by(OsintFinding.analyzed_at, OsintFinding.id)
        )
        return RegistroOsint(
            [desde_osint_finding(f) for f in filas], FuenteOsint.FINDINGS
        )

    return RegistroOsint([], FuenteOsint.NO_DISPONIBLE)


def get_tracking_events(db: Session, case_id: int) -> list[TrackingEvent]:
    stmt = (
        select(TrackingEvent)
        .where(TrackingEvent.case_id == case_id)
        .order_by(TrackingEvent.hora, TrackingEvent.id)
    )
    return list(db.scalars(stmt))


def next_version(db: Session, case_id: int) -> int:
    max_version = db.scalar(
        select(func.max(Report.version)).where(Report.case_id == case_id)
    )
    return (max_version or 0) + 1


def reservar_report(
    db: Session,
    case_id: int,
    resumen_ia: str,
    archivo_pdf: str,
    generado_por: str,
    version: int,
    fecha_generacion: datetime,
    notas: str | None = None,
    opciones: dict | None = None,
) -> Report:
    """
    Inserta la fila y hace `flush`, **sin confirmar**.

    El `flush` es lo que reserva el número de versión: si otra generación
    simultánea ya se quedó con él, la restricción única salta aquí, antes de
    que este proceso escriba sus ficheros. Si escribiéramos primero, el
    perdedor de la carrera habría sobrescrito los documentos del ganador con
    los suyos, y la fila del ganador acabaría apuntando a un informe que no es
    el que declara. Confirmar es cosa del servicio, cuando los ficheros ya
    están en disco.
    """
    report = Report(
        case_id=case_id,
        resumen_ia=resumen_ia,
        archivo_pdf=archivo_pdf,
        generado_por=generado_por,
        version=version,
        fecha_generacion=fecha_generacion,
        notas=notas,
        opciones=opciones,
    )
    db.add(report)
    db.flush()
    return report


def get_report(db: Session, report_id: int) -> Report | None:
    return db.get(Report, report_id)


def list_reports_for_case(db: Session, case_id: int) -> list[Report]:
    stmt = (
        select(Report)
        .where(Report.case_id == case_id)
        .order_by(Report.version)
    )
    return list(db.scalars(stmt))
