"""
Endpoints de Timeline.

Auditoría Módulo 4 (2026-09-27):
- H-04: el handler del refresh ya no filtra `str(e)` al cliente (podía
  exponer host/puerto/usuario de MySQL o fragmentos de SQL). Devuelve un
  mensaje genérico; el detalle va al log del servidor.
- H-13: `case_id` se valida con `Path(..., gt=0)` en ambos endpoints.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.timeline import repository, schemas, service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/cases/{case_id}", response_model=List[schemas.TimelineEventResponse])
def get_timeline(
    case_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    return repository.get_timeline_events(db, case_id)


@router.post("/cases/{case_id}/refresh", response_model=List[schemas.TimelineEventResponse])
def refresh_timeline(
    case_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    try:
        return service.refresh_timeline(db, case_id)
    except Exception:
        logger.exception("Error al refrescar la timeline (case_id=%s)", case_id)
        raise HTTPException(
            status_code=500,
            detail="Error al recalcular la línea temporal",
        )
