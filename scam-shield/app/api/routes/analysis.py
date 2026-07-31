from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import Case
from app.schemas.domain_analysis import CaseResponse, DomainAnalysisRequest
from app.services.domain_analysis_service import run_domain_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/domain", response_model=CaseResponse)
def analyze_domain(payload: DomainAnalysisRequest, db: Session = Depends(get_db)) -> Case:
    return run_domain_analysis(db, payload.domain)
