from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.phone import service
from app.modules.osint.phone.models import PhoneCase
from app.modules.osint.phone.schemas import PhoneAnalysisRequest, PhoneCaseListItem, PhoneCaseResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/phone-cases", tags=["phone-cases"])


@router.post("/phone", response_model=PhoneCaseResponse)
def analyze_phone(payload: PhoneAnalysisRequest, db: Session = Depends(get_db)) -> PhoneCase:
    try:
        return service.run_phone_analysis(db, payload.phone, payload.default_region, case_id=payload.case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[PhoneCaseListItem])
def list_phone_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=PhoneCaseResponse)
def get_phone_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de teléfono {case_id}")
    return case
