from sqlalchemy.orm import Session

from app.modules.cases import repository
from app.modules.cases.integrity import ALGORITMO, calcular_hash_valor
from app.modules.cases.models import AccionAuditoria, Case, CaseAuditLog, EstadoCaso, Evidence
from app.modules.cases.schemas import (
    CaseCreate,
    CaseUpdate,
    EvidenceCreate,
    EvidenceIntegrityCheck,
    EvidenceUpdate,
    OsintVinculacionAudit,
)
from app.modules.cases.state_machine import validar_transicion

ACTOR_POR_DEFECTO = "api"


class CaseNotFoundError(Exception):
    pass


class EvidenceNotFoundError(Exception):
    pass


class CaseDeletedError(Exception):
    """El caso existe pero está eliminado (lógicamente): no admite nuevas
    operaciones de escritura sobre él ni sobre sus evidencias."""

    def __init__(self, case_id: int):
        self.case_id = case_id
        super().__init__(f"El caso {case_id} está eliminado")


class EvidenceDeletedError(Exception):
    def __init__(self, evidence_id: int):
        self.evidence_id = evidence_id
        super().__init__(f"La evidencia {evidence_id} está eliminada")


class CaseArchivedError(Exception):
    """Un caso ARCHIVADO es un registro histórico cerrado: inmutable salvo
    para el propio borrado lógico."""

    def __init__(self, case_id: int):
        self.case_id = case_id
        super().__init__(f"El caso {case_id} está archivado y no admite modificaciones")


def create_case(db: Session, data: CaseCreate, *, actor: str = ACTOR_POR_DEFECTO) -> Case:
    case = repository.create_case(db, data)
    repository.add_audit_entry(
        db,
        case_id=case.id,
        accion=AccionAuditoria.CASE_CREADO,
        actor=actor,
        detalle={"estado": case.estado.value},
    )
    return case


def get_case(db: Session, case_id: int) -> Case:
    case = repository.get_case(db, case_id)
    if case is None:
        raise CaseNotFoundError(case_id)
    return case


def get_active_case(db: Session, case_id: int) -> Case:
    """Como get_case, pero además exige que el caso no esté eliminado.
    Úsalo en cualquier operación de escritura sobre el caso o sus
    evidencias; get_case por sí sola se sigue usando para poder *ver* un
    caso eliminado (auditoría/inspección)."""
    case = get_case(db, case_id)
    if case.eliminado:
        raise CaseDeletedError(case_id)
    return case


def list_cases(db: Session, skip: int = 0, limit: int = 100, incluir_eliminados: bool = False) -> list[Case]:
    return repository.list_cases(db, skip, limit, incluir_eliminados)


def update_case(db: Session, case_id: int, data: CaseUpdate, *, actor: str = ACTOR_POR_DEFECTO) -> Case:
    case = get_active_case(db, case_id)
    if case.estado == EstadoCaso.ARCHIVADO:
        raise CaseArchivedError(case_id)

    payload = data.model_dump(exclude_unset=True)
    estado_anterior = case.estado
    nuevo_estado = payload.get("estado")
    if nuevo_estado is not None and nuevo_estado != estado_anterior:
        validar_transicion(estado_anterior, nuevo_estado)

    updated = repository.update_case(db, case, data)

    campos_no_estado = [campo for campo in payload if campo != "estado"]
    if campos_no_estado:
        repository.add_audit_entry(
            db,
            case_id=case.id,
            accion=AccionAuditoria.CASE_ACTUALIZADO,
            actor=actor,
            detalle={"campos": campos_no_estado},
        )
    if nuevo_estado is not None and nuevo_estado != estado_anterior:
        repository.add_audit_entry(
            db,
            case_id=case.id,
            accion=AccionAuditoria.CASE_ESTADO_CAMBIADO,
            actor=actor,
            detalle={"de": estado_anterior.value, "a": nuevo_estado.value},
        )

    return updated


def delete_case(db: Session, case_id: int, *, actor: str = ACTOR_POR_DEFECTO) -> None:
    case = get_case(db, case_id)
    if case.eliminado:
        raise CaseDeletedError(case_id)
    evidence_ids = [e.id for e in case.evidences if not e.eliminado]
    repository.soft_delete_case(db, case)
    repository.add_audit_entry(
        db,
        case_id=case.id,
        accion=AccionAuditoria.CASE_ELIMINADO,
        actor=actor,
        detalle={"evidencias_afectadas": evidence_ids} if evidence_ids else None,
    )


def create_evidence(
    db: Session, case_id: int, data: EvidenceCreate, *, actor: str = ACTOR_POR_DEFECTO
) -> Evidence:
    get_active_case(db, case_id)
    evidence = repository.create_evidence(db, case_id, data)
    repository.add_audit_entry(
        db,
        case_id=case_id,
        evidence_id=evidence.id,
        accion=AccionAuditoria.EVIDENCE_CREADA,
        actor=actor,
        detalle={"tipo": evidence.tipo},
    )
    return evidence


def get_evidence(db: Session, case_id: int, evidence_id: int) -> Evidence:
    get_case(db, case_id)
    evidence = repository.get_evidence(db, evidence_id)
    if evidence is None or evidence.case_id != case_id:
        raise EvidenceNotFoundError(evidence_id)
    return evidence


def list_evidences(
    db: Session, case_id: int, skip: int = 0, limit: int = 100, incluir_eliminados: bool = False
) -> list[Evidence]:
    get_case(db, case_id)
    return repository.list_evidences_by_case(db, case_id, skip, limit, incluir_eliminados)


def update_evidence(
    db: Session,
    case_id: int,
    evidence_id: int,
    data: EvidenceUpdate,
    *,
    actor: str = ACTOR_POR_DEFECTO,
) -> Evidence:
    get_active_case(db, case_id)
    evidence = get_evidence(db, case_id, evidence_id)
    if evidence.eliminado:
        raise EvidenceDeletedError(evidence_id)

    payload = data.model_dump(exclude_unset=True)
    updated = repository.update_evidence(db, evidence, data)
    if payload:
        repository.add_audit_entry(
            db,
            case_id=case_id,
            evidence_id=evidence.id,
            accion=AccionAuditoria.EVIDENCE_ACTUALIZADA,
            actor=actor,
            detalle={"campos": list(payload.keys())},
        )
    return updated


def delete_evidence(
    db: Session, case_id: int, evidence_id: int, *, actor: str = ACTOR_POR_DEFECTO
) -> None:
    get_case(db, case_id)
    evidence = get_evidence(db, case_id, evidence_id)
    if evidence.eliminado:
        raise EvidenceDeletedError(evidence_id)
    repository.soft_delete_evidence(db, evidence)
    repository.add_audit_entry(
        db,
        case_id=case_id,
        evidence_id=evidence.id,
        accion=AccionAuditoria.EVIDENCE_ELIMINADA,
        actor=actor,
    )


def verify_evidence_integrity(db: Session, case_id: int, evidence_id: int) -> EvidenceIntegrityCheck:
    evidence = get_evidence(db, case_id, evidence_id)
    hash_actual = calcular_hash_valor(evidence.valor)
    return EvidenceIntegrityCheck(
        evidence_id=evidence.id,
        algoritmo=ALGORITMO,
        hash_registrado=evidence.hash_valor,
        hash_actual=hash_actual,
        integro=hash_actual == evidence.hash_valor,
    )


def list_audit_log(db: Session, case_id: int) -> list[CaseAuditLog]:
    get_case(db, case_id)
    return repository.list_audit_log(db, case_id)


class InvalidOsintAuditPayloadError(Exception):
    """`case_anterior`/`case_nuevo` no describen un cambio real, o ninguno
    de los dos coincide con el case_id de la URL."""


def registrar_vinculacion_osint(
    db: Session, case_id: int, data: OsintVinculacionAudit, *, actor: str
) -> CaseAuditLog:
    """
    Registra en case_audit_log un cambio de vinculación de una investigación
    OSINT (scam-shield) con este caso — ver OsintVinculacionAudit. No toca
    ninguna tabla de OSINT (ese cambio ya lo persistió scam-shield antes de
    llamar aquí): esto es solo la entrada de auditoría.

    `actor` lo resuelve la ruta (ver auth/dependencies.py::
    resolve_osint_actor) a partir del JWT reenviado por OSINT — nunca del
    body de la petición.

    get_case (no get_active_case): un caso eliminado o archivado sigue
    pudiendo recibir esta entrada — p. ej. al desvincular una investigación
    de un caso que mientras tanto se archivó o se eliminó lógicamente, el
    hecho sigue siendo real y debe quedar auditado.
    """
    get_case(db, case_id)

    if data.case_anterior is None and data.case_nuevo is None:
        raise InvalidOsintAuditPayloadError("case_anterior y case_nuevo no pueden ser ambos nulos")
    if case_id not in (data.case_anterior, data.case_nuevo):
        raise InvalidOsintAuditPayloadError(
            f"el case_id de la URL ({case_id}) no coincide con case_anterior ni case_nuevo"
        )

    return repository.add_audit_entry(
        db,
        case_id=case_id,
        accion=AccionAuditoria.OSINT_VINCULACION_CAMBIADA,
        actor=actor,
        detalle={
            "case_type": data.case_type,
            "source_id": data.source_id,
            "subject_value": data.subject_value,
            "de": data.case_anterior,
            "a": data.case_nuevo,
        },
    )
