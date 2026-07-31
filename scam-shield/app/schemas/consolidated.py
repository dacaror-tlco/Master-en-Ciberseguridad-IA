from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import RiskFlag


class ConsolidatedRequest(BaseModel):
    domain_case_ids: list[int] = Field(default_factory=list)
    email_case_ids: list[int] = Field(default_factory=list)
    wallet_case_ids: list[int] = Field(default_factory=list)
    typosquatting_case_ids: list[int] = Field(default_factory=list)
    victim_notes: Optional[str] = None
    include_ai_narrative: bool = Field(
        True, description="Si es False, se omite la llamada al LLM (útil para no gastar API calls al probar)"
    )


class ConsolidatedResponse(BaseModel):
    consolidated_score: int = Field(..., ge=0, le=100)
    correlation_flags: list[RiskFlag] = []
    ai_narrative: Optional[str] = None
    ai_narrative_error: Optional[str] = Field(
        None, description="Si la narrativa de IA falló (p.ej. sin API key), el motivo se explica aquí sin tumbar el resto de la respuesta"
    )
