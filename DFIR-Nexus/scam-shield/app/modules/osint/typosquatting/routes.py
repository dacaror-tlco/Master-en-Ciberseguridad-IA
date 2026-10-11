from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.typosquatting import service
from app.modules.osint.typosquatting.models import TyposquattingCase
from app.modules.osint.typosquatting.schemas import (
    TyposquattingCaseListItem,
    TyposquattingCaseResponse,
    TyposquattingRequest,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/typosquatting-cases", tags=["typosquatting-cases"])


@router.post("/typosquatting", response_model=TyposquattingCaseResponse)
def analyze_typosquatting(payload: TyposquattingRequest, db: Session = Depends(get_db)) -> TyposquattingCase:
    try:
        return service.run_typosquatting_analysis(
            db,
            payload.domain,
            max_variants=payload.max_variants,
            include_full_analysis=payload.include_full_analysis,
            max_full_analysis=payload.max_full_analysis,
            max_ip_checks=payload.max_ip_checks,
            case_id=payload.case_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[TyposquattingCaseListItem])
def list_typosquatting_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=TyposquattingCaseResponse)
def get_typosquatting_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de typosquatting {case_id}")
    return case
