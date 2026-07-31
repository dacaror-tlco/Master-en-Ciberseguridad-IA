from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cnmv_check_case import CnmvCheckCase
from app.models.cnmv_warning import CnmvWarning
from app.schemas.cnmv import (
    CnmvCheckCaseListItem,
    CnmvCheckCaseResponse,
    CnmvCheckRequest,
)
from app.services.cnmv_analysis_service import run_cnmv_check

router = APIRouter(prefix="/analysis", tags=["cnmv"])
cases_router = APIRouter(prefix="/cnmv-check-cases", tags=["cnmv"])
warnings_router = APIRouter(prefix="/cnmv-warnings", tags=["cnmv"])


@router.post("/cnmv-check", response_model=CnmvCheckCaseResponse)
def check_cnmv(payload: CnmvCheckRequest, db: Session = Depends(get_db)) -> CnmvCheckCase:
    try:
        return run_cnmv_check(db, payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[CnmvCheckCaseListItem])
def list_cnmv_check_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(CnmvCheckCase)
        .order_by(desc(CnmvCheckCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=CnmvCheckCaseResponse)
def get_cnmv_check_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(CnmvCheckCase).filter(CnmvCheckCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso {case_id}")
    return case


@warnings_router.get("/cache-status")
def cnmv_cache_status(db: Session = Depends(get_db)):
    """Útil para depurar: cuántas advertencias hay en caché local y de cuándo son."""
    count = db.query(CnmvWarning).count()
    newest = db.query(CnmvWarning).order_by(desc(CnmvWarning.scraped_at)).first()
    return {
        "cached_warnings": count,
        "last_refreshed": newest.scraped_at.isoformat() if newest else None,
    }
