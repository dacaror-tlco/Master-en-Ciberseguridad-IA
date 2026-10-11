from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.domain import service
from app.modules.osint.domain.models import Case
from app.modules.osint.domain.schemas import CaseListItem, CaseResponse, DomainAnalysisRequest

router = APIRouter(prefix="/analysis", tags=["analysis"])
# Antes "/cases": colisionaba con el `/cases` de Casos (Módulo 1) en el
# gateway/namespace común de Nexus (ver docs/CONTRATOS.md, integración
# Fase 1). Renombrado siguiendo el mismo patrón que ya usan el resto de
# sub-módulos de OSINT (`/email-cases`, `/wallet-cases`, `/phone-cases`...),
# y alineado con el nombre real de la tabla, `osint_domain_cases`.
cases_router = APIRouter(prefix="/domain-analysis-cases", tags=["domain-analysis-cases"])


@router.post("/domain", response_model=CaseResponse)
def analyze_domain(payload: DomainAnalysisRequest, db: Session = Depends(get_db)) -> Case:
    return service.run_domain_analysis(db, payload.domain, case_id=payload.case_id)


@cases_router.get("", response_model=list[CaseListItem])
def list_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lista los casos analizados, más recientes primero."""
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Recupera el detalle completo de un caso concreto (para el informe PDF, más adelante)."""
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso {case_id}")
    return case
