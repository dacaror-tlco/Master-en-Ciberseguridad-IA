from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.phone_case import PhoneCase
from app.schemas.phone_analysis import PhoneAnalysisRequest, PhoneCaseListItem, PhoneCaseResponse
from app.services.phone_analysis_service import run_phone_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/phone-cases", tags=["phone-cases"])


@router.post("/phone", response_model=PhoneCaseResponse)
def analyze_phone(payload: PhoneAnalysisRequest, db: Session = Depends(get_db)) -> PhoneCase:
    try:
        return run_phone_analysis(db, payload.phone, payload.default_region)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[PhoneCaseListItem])
def list_phone_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(PhoneCase)
        .order_by(desc(PhoneCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=PhoneCaseResponse)
def get_phone_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(PhoneCase).filter(PhoneCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de teléfono {case_id}")
    return case
