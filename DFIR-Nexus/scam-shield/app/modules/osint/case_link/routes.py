from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.case_link import schemas, service

router = APIRouter(prefix="/osint-cases", tags=["osint-case-link"])


@router.patch("/{case_type}/{id}/vinculacion", response_model=schemas.VinculacionUpdateResponse)
def actualizar_vinculacion(
    case_type: str,
    id: int,
    data: schemas.VinculacionUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> schemas.VinculacionUpdateResponse:
    """
    Vincula, cambia o desvincula (case_id=null) una investigación OSINT
    con un caso de Nexus. Genérico para los 8 tipos de investigación (ver
    service.CASE_TYPES) — un único endpoint en vez de ocho casi idénticos.
    """
    try:
        investigacion, cambiado, case_anterior = service.actualizar_vinculacion(
            db, case_type, id, data.case_id
        )
    except service.UnknownCaseTypeError:
        raise HTTPException(status_code=404, detail=f"Tipo de investigación desconocido: {case_type!r}")
    except service.InvestigationNotFoundError:
        raise HTTPException(status_code=404, detail=f"No existe la investigación {case_type}#{id}")
    except service.TargetCaseNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No existe el caso {data.case_id}, o está eliminado",
        )

    if not cambiado:
        return schemas.VinculacionUpdateResponse(
            case_type=case_type, id=id, case_id=investigacion.case_id, cambiado=False,
        )

    auditoria_ok, auditoria_error = service.registrar_auditoria(
        case_type=case_type,
        investigacion=investigacion,
        case_anterior=case_anterior,
        case_nuevo=data.case_id,
        # Reenvía tal cual el JWT del usuario que disparó este cambio (ya
        # validado por la dependencia de router de este endpoint, ver
        # main.py) — Casos lo usa para resolver el `actor` real de la
        # entrada de auditoría en vez de "osint" (ver audit_client.py).
        authorization_header=request.headers.get("Authorization"),
    )
    return schemas.VinculacionUpdateResponse(
        case_type=case_type,
        id=id,
        case_id=investigacion.case_id,
        cambiado=True,
        auditoria_registrada=auditoria_ok,
        auditoria_error=auditoria_error,
    )
