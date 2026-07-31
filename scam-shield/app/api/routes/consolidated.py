from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import Case
from app.models.email_case import EmailCase
from app.models.typosquatting_case import TyposquattingCase
from app.models.wallet_case import WalletCase
from app.schemas.consolidated import ConsolidatedRequest, ConsolidatedResponse
from app.services import ai_service
from app.services.correlation_service import find_correlations

router = APIRouter(prefix="/analysis", tags=["consolidated"])


@router.post("/consolidated", response_model=ConsolidatedResponse)
def consolidated_assessment(payload: ConsolidatedRequest, db: Session = Depends(get_db)) -> ConsolidatedResponse:
    if not (payload.domain_case_ids or payload.email_case_ids or payload.wallet_case_ids or payload.typosquatting_case_ids):
        raise HTTPException(status_code=400, detail="Indica al menos un caso (dominio, email, wallet o typosquatting) para el análisis consolidado")

    domain_cases = db.query(Case).filter(Case.id.in_(payload.domain_case_ids)).all() if payload.domain_case_ids else []
    email_cases = db.query(EmailCase).filter(EmailCase.id.in_(payload.email_case_ids)).all() if payload.email_case_ids else []
    wallet_cases = db.query(WalletCase).filter(WalletCase.id.in_(payload.wallet_case_ids)).all() if payload.wallet_case_ids else []
    typosquatting_cases = (
        db.query(TyposquattingCase).filter(TyposquattingCase.id.in_(payload.typosquatting_case_ids)).all()
        if payload.typosquatting_case_ids else []
    )

    all_scores = [c.risk_score for c in (*domain_cases, *email_cases, *wallet_cases, *typosquatting_cases)]
    base_score = max(all_scores) if all_scores else 0

    correlation_flags = find_correlations(domain_cases, email_cases, wallet_cases, typosquatting_cases)
    # La correlación entre módulos sube el score base: es una señal más fuerte
    # que cualquier señal aislada, porque confirma que es la misma infraestructura.
    consolidated_score = min(base_score + (15 if correlation_flags else 0), 100)

    narrative = None
    narrative_error = None
    if payload.include_ai_narrative:
        try:
            narrative = ai_service.generate_narrative(
                domain_cases, email_cases, wallet_cases, correlation_flags, payload.victim_notes
            )
        except Exception as exc:
            narrative_error = str(exc)

    return ConsolidatedResponse(
        consolidated_score=consolidated_score,
        correlation_flags=correlation_flags,
        ai_narrative=narrative,
        ai_narrative_error=narrative_error,
    )
