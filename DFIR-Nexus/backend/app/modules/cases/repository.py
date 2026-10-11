from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.cases.integrity import calcular_hash_valor
from app.modules.cases.models import AccionAuditoria, Case, CaseAuditLog, Evidence
from app.modules.cases.schemas import CaseCreate, CaseUpdate, EvidenceCreate, EvidenceUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_case(db: Session, data: CaseCreate) -> Case:
    case = Case(**data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> Case | None:
    return db.get(Case, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 100, incluir_eliminados: bool = False) -> list[Case]:
    query = db.query(Case)
    if not incluir_eliminados:
        query = query.filter(Case.eliminado.is_(False))
    return query.order_by(Case.id).offset(skip).limit(limit).all()


def update_case(db: Session, case: Case, data: CaseUpdate) -> Case:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case


def soft_delete_case(db: Session, case: Case) -> Case:
    """
    Borrado LÓGICO únicamente: nunca se emite un DELETE físico sobre
    `cases`. Es la corrección de raíz del 500 histórico en
    `DELETE /cases/{id}` — ese 500 ocurría porque `tracking_events` y
    `reports` (backends independientes, misma base de datos compartida)
    tienen FKs a `cases.id` SIN `ondelete=CASCADE`; un DELETE físico de un
    caso con esos dependientes violaba integridad referencial y MySQL lo
    rechazaba. Al no borrar nunca físicamente, esa constraint no se
    ejercita jamás desde este flujo.

    Cascada LÓGICA (no de base de datos) a las evidencias del caso: un
    caso eliminado no debe dejar evidencias "activas" sueltas.
    """
    now = _now()
    case.eliminado = True
    case.fecha_eliminacion = now
    for evidence in case.evidences:
        if not evidence.eliminado:
            evidence.eliminado = True
            evidence.fecha_eliminacion = now
    db.commit()
    db.refresh(case)
    return case


def create_evidence(db: Session, case_id: int, data: EvidenceCreate) -> Evidence:
    payload = data.model_dump()
    evidence = Evidence(case_id=case_id, hash_valor=calcular_hash_valor(payload["valor"]), **payload)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_evidence(db: Session, evidence_id: int) -> Evidence | None:
    return db.get(Evidence, evidence_id)


def list_evidences_by_case(
    db: Session, case_id: int, skip: int = 0, limit: int = 100, incluir_eliminados: bool = False
) -> list[Evidence]:
    query = db.query(Evidence).filter(Evidence.case_id == case_id)
    if not incluir_eliminados:
        query = query.filter(Evidence.eliminado.is_(False))
    return query.order_by(Evidence.id).offset(skip).limit(limit).all()


def update_evidence(db: Session, evidence: Evidence, data: EvidenceUpdate) -> Evidence:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(evidence, field, value)
    db.commit()
    db.refresh(evidence)
    return evidence


def soft_delete_evidence(db: Session, evidence: Evidence) -> Evidence:
    evidence.eliminado = True
    evidence.fecha_eliminacion = _now()
    db.commit()
    db.refresh(evidence)
    return evidence


def add_audit_entry(
    db: Session,
    *,
    case_id: int,
    accion: AccionAuditoria,
    actor: str,
    evidence_id: int | None = None,
    detalle: dict | None = None,
) -> CaseAuditLog:
    """
    Se llama siempre DESPUÉS de que el cambio de negocio que documenta ya
    esté confirmado (case_id/evidence_id reales, incluyendo altas donde el
    id solo existe tras el primer commit). Hace su propio commit: es una
    simplificación deliberada — no es estrictamente atómica con la operación
    que audita, pero mantiene el código legible y proporcional al alcance de
    esta tarea. Ver informe final: limitación conocida, no una garantía de
    atomicidad estricta.
    """
    entry = CaseAuditLog(
        case_id=case_id,
        evidence_id=evidence_id,
        accion=accion,
        actor=actor,
        detalle=detalle,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_log(db: Session, case_id: int) -> list[CaseAuditLog]:
    return (
        db.query(CaseAuditLog)
        .filter(CaseAuditLog.case_id == case_id)
        .order_by(CaseAuditLog.creado_en.desc(), CaseAuditLog.id.desc())
        .all()
    )
