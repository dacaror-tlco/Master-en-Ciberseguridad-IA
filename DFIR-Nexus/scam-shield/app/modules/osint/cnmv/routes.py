from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.cnmv import service
from app.modules.osint.cnmv.models import CnmvCheckCase
from app.modules.osint.cnmv.schemas import (
    CnmvCheckCaseListItem,
    CnmvCheckCaseResponse,
    CnmvCheckRequest,
)

router = APIRouter(prefix="/analysis", tags=["cnmv"])
cases_router = APIRouter(prefix="/cnmv-check-cases", tags=["cnmv"])
warnings_router = APIRouter(prefix="/cnmv-warnings", tags=["cnmv"])


@router.post("/cnmv-check", response_model=CnmvCheckCaseResponse)
def check_cnmv(payload: CnmvCheckRequest, db: Session = Depends(get_db)) -> CnmvCheckCase:
    try:
        return service.run_cnmv_check(db, payload.query, case_id=payload.case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[CnmvCheckCaseListItem])
def list_cnmv_check_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=CnmvCheckCaseResponse)
def get_cnmv_check_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso {case_id}")
    return case


@warnings_router.get("/cache-status")
def cnmv_cache_status(db: Session = Depends(get_db)):
    """Útil para depurar: cuántas advertencias hay en caché local y de cuándo son."""
    return service.cache_status(db)
