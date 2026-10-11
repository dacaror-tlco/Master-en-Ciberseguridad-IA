"""
Schemas de generación de informe (PDF combinado) y de valoración
consolidada con IA. Antes en app/schemas/{report,consolidated}.py.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.osint.shared.schemas import RiskFlag


class ReportRequest(BaseModel):
    """
    El usuario elige qué casos de cada módulo (dominio, email, wallet...)
    quiere incluir en un único PDF — normalmente porque están todos
    relacionados con la misma estafa (ej: el dominio del sitio falso + el
    email que lo promocionaba + la wallet a la que pedían transferir el
    dinero).
    """
    domain_case_ids: list[int] = Field(default_factory=list)
    email_case_ids: list[int] = Field(default_factory=list)
    wallet_case_ids: list[int] = Field(default_factory=list)
    typosquatting_case_ids: list[int] = Field(default_factory=list)
    phone_case_ids: list[int] = Field(default_factory=list)
    cnmv_check_case_ids: list[int] = Field(default_factory=list)
    image_case_ids: list[int] = Field(default_factory=list)
    ip_case_ids: list[int] = Field(default_factory=list)
    victim_notes: Optional[str] = Field(
        None,
        description="Espacio libre para que la víctima describa qué pasó, en sus propias palabras (se incluye tal cual en el informe).",
    )
    ai_narrative: Optional[str] = Field(
        None,
        description="Narrativa generada por /analysis/consolidated (opcional). Si se incluye, se añade como sección en la portada del informe.",
    )


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
