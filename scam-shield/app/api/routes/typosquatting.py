from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.typosquatting_case import TyposquattingCase
from app.schemas.typosquatting import (
    TyposquattingCaseListItem,
    TyposquattingCaseResponse,
    TyposquattingRequest,
)
from app.services.typosquatting_analysis_service import run_typosquatting_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/typosquatting-cases", tags=["typosquatting-cases"])


@router.post("/typosquatting", response_model=TyposquattingCaseResponse)
def analyze_typosquatting(payload: TyposquattingRequest, db: Session = Depends(get_db)) -> TyposquattingCase:
    try:
        return run_typosquatting_analysis(
            db,
            payload.domain,
            max_variants=payload.max_variants,
            include_full_analysis=payload.include_full_analysis,
            max_full_analysis=payload.max_full_analysis,
            max_ip_checks=payload.max_ip_checks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[TyposquattingCaseListItem])
def list_typosquatting_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(TyposquattingCase)
        .order_by(desc(TyposquattingCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=TyposquattingCaseResponse)
def get_typosquatting_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TyposquattingCase).filter(TyposquattingCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de typosquatting {case_id}")
    return case
