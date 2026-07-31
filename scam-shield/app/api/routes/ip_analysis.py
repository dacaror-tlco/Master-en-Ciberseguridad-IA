from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ip_case import IpCase
from app.schemas.ip_analysis import IpAnalysisRequest, IpCaseListItem, IpCaseResponse
from app.services.ip_analysis_service import run_ip_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/ip-cases", tags=["ip-cases"])


@router.post("/ip", response_model=IpCaseResponse)
def analyze_ip(payload: IpAnalysisRequest, db: Session = Depends(get_db)) -> IpCase:
    try:
        return run_ip_analysis(db, payload.ip)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@cases_router.get("", response_model=list[IpCaseListItem])
def list_ip_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(IpCase)
        .order_by(desc(IpCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=IpCaseResponse)
def get_ip_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(IpCase).filter(IpCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de IP {case_id}")
    return case
