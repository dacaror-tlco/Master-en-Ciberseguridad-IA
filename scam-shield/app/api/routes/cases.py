from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import Case
from app.schemas.domain_analysis import CaseListItem, CaseResponse

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[CaseListItem])
def list_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lista los casos analizados, más recientes primero."""
    return (
        db.query(Case)
        .order_by(desc(Case.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Recupera el detalle completo de un caso concreto (para el informe PDF, más adelante)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso {case_id}")
    return case
