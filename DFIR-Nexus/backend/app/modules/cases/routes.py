from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, require_admin, resolve_osint_actor
from app.modules.auth.models import User
from app.modules.cases import service
from app.modules.cases.schemas import (
    AuditLogEntry,
    CaseCreate,
    CaseRead,
    CaseUpdate,
    EvidenceCreate,
    EvidenceIntegrityCheck,
    EvidenceRead,
    EvidenceUpdate,
    OsintVinculacionAudit,
)
from app.modules.cases.service import (
    CaseArchivedError,
    CaseDeletedError,
    CaseNotFoundError,
    EvidenceDeletedError,
    EvidenceNotFoundError,
    InvalidOsintAuditPayloadError,
)
from app.modules.cases.state_machine import InvalidStateTransitionError

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    data: CaseCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> CaseRead:
    return service.create_case(db, data)


@router.get("", response_model=list[CaseRead])
def list_cases(
    skip: int = 0,
    limit: int = 100,
    incluir_eliminados: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[CaseRead]:
    return service.list_cases(db, skip, limit, incluir_eliminados)


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> CaseRead:
    try:
        return service.get_case(db, case_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")


@router.put("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int, data: CaseUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> CaseRead:
    try:
        return service.update_case(db, case_id, data)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except CaseDeletedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El caso está eliminado")
    except CaseArchivedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El caso está archivado: es un registro histórico inmutable",
        )
    except InvalidStateTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transición de estado no permitida: {exc.actual.value} -> {exc.nuevo.value}",
        )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)) -> None:
    """
    Borrado LÓGICO (ver service.delete_case): el caso deja de estar activo
    y desaparece de los listados por defecto, pero el registro y su
    historial de auditoría se conservan siempre.

    Único DELETE de este módulo que exige admin (ver matriz de permisos):
    borra un caso completo, visible para cualquiera con acceso — a
    diferencia de DELETE de una evidencia concreta (más localizado, ver
    delete_evidence más abajo, que solo exige estar autenticado).
    """
    try:
        service.delete_case(db, case_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except CaseDeletedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El caso ya estaba eliminado")


@router.get("/{case_id}/auditoria", response_model=list[AuditLogEntry])
def get_case_audit_log(
    case_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> list[AuditLogEntry]:
    try:
        return service.list_audit_log(db, case_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")


@router.post(
    "/{case_id}/auditoria/osint", response_model=AuditLogEntry, status_code=status.HTTP_201_CREATED
)
def registrar_vinculacion_osint(
    case_id: int,
    data: OsintVinculacionAudit,
    db: Session = Depends(get_db),
    actor: str = Depends(resolve_osint_actor),
) -> AuditLogEntry:
    """
    Endpoint estrecho: solo registra en case_audit_log un cambio de
    vinculación de una investigación OSINT con este caso (ver
    schemas.OsintVinculacionAudit). Lo llama scam-shield por HTTP tras
    persistir el cambio en su propia base — nunca al revés, y nunca para
    ninguna otra acción de auditoría.

    Deliberadamente SIN require_admin ni get_current_user: es una llamada
    servidor→servidor de OSINT, no de un usuario final — meterla en la
    autorización normal de usuario la dejaría inservible para OSINT (que
    no tiene, ni debe tener, credenciales de usuario de Nexus) o, peor, la
    abriría a cualquiera con un JWT de analyst/admin válido para falsear
    auditoría en nombre de OSINT. En su lugar, `resolve_osint_actor`
    (Fase 4) exige el `X-Service-Token` propio de esta integración y,
    aparte, intenta resolver el JWT de usuario reenviado por OSINT
    únicamente para rellenar `actor` con el nombre real — nunca como
    condición de acceso.
    """
    try:
        return service.registrar_vinculacion_osint(db, case_id, data, actor=actor)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except InvalidOsintAuditPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/{case_id}/evidences", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED
)
def create_evidence(
    case_id: int,
    data: EvidenceCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EvidenceRead:
    try:
        return service.create_evidence(db, case_id, data)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except CaseDeletedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El caso está eliminado: no se pueden añadir evidencias",
        )


@router.get("/{case_id}/evidences", response_model=list[EvidenceRead])
def list_evidences(
    case_id: int,
    skip: int = 0,
    limit: int = 100,
    incluir_eliminados: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[EvidenceRead]:
    try:
        return service.list_evidences(db, case_id, skip, limit, incluir_eliminados)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")


@router.get("/{case_id}/evidences/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    case_id: int, evidence_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> EvidenceRead:
    try:
        return service.get_evidence(db, case_id, evidence_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except EvidenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")


@router.get("/{case_id}/evidences/{evidence_id}/integridad", response_model=EvidenceIntegrityCheck)
def verify_evidence_integrity(
    case_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EvidenceIntegrityCheck:
    """Recalcula sha256(valor) y lo compara con el hash registrado al crear
    la evidencia. `integro=False` significa que `valor` cambió por una vía
    que no fue el API normal (éste nunca lo permite tras la creación)."""
    try:
        return service.verify_evidence_integrity(db, case_id, evidence_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except EvidenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")


@router.put("/{case_id}/evidences/{evidence_id}", response_model=EvidenceRead)
def update_evidence(
    case_id: int,
    evidence_id: int,
    data: EvidenceUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EvidenceRead:
    try:
        return service.update_evidence(db, case_id, evidence_id, data)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except EvidenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
    except CaseDeletedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El caso está eliminado")
    except EvidenceDeletedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La evidencia está eliminada")


@router.delete("/{case_id}/evidences/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    case_id: int, evidence_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> None:
    """
    A diferencia de DELETE /cases/{id}, no exige admin: es una corrección
    localizada sobre una evidencia concreta (ver matriz de permisos),
    no la baja de todo un caso compartido.
    """
    try:
        service.delete_evidence(db, case_id, evidence_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado")
    except EvidenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
    except EvidenceDeletedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La evidencia ya estaba eliminada")
