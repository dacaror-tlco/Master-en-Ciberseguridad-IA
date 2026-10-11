from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.ip import service
from app.modules.osint.ip.models import IpCase
from app.modules.osint.ip.schemas import IpAnalysisRequest, IpCaseListItem, IpCaseResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/ip-cases", tags=["ip-cases"])


@router.post("/ip", response_model=IpCaseResponse)
def analyze_ip(payload: IpAnalysisRequest, db: Session = Depends(get_db)) -> IpCase:
    try:
        return service.run_ip_analysis(db, payload.ip, case_id=payload.case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[IpCaseListItem])
def list_ip_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=IpCaseResponse)
def get_ip_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de IP {case_id}")
    return case
