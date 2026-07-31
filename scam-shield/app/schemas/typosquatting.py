from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import AbuseIpInfo, RiskFlag


class TyposquattingRequest(BaseModel):
    domain: str = Field(..., description="Dominio legítimo a proteger (la marca real)", examples=["bbva.es"])
    include_full_analysis: bool = Field(
        False,
        description="Si es True, corre WHOIS/SSL/VirusTotal en las variantes que resuelven (limitado a max_full_analysis, para no agotar límites de API gratuitos)",
    )
    max_variants: int = Field(200, le=500, description="Tope de variantes a generar")
    max_full_analysis: int = Field(4, le=10, description="Cuántas variantes resueltas analizar en profundidad como máximo")
    max_ip_checks: int = Field(
        50, le=200,
        description="Tope de IPs únicas a consultar en AbuseIPDB — mucho más barato que el análisis completo (WHOIS/SSL/VirusTotal), así que el límite es más generoso que max_full_analysis",
    )


class TyposquattingCandidate(BaseModel):
    variant: str
    technique: str
    resolves: bool
    ip_address: Optional[str] = None
    # Reputación de IP (AbuseIPDB) — barata, se calcula para TODAS las
    # variantes resueltas (hasta max_ip_checks IPs únicas), no solo las
    # analizadas en profundidad. Ver fully_analyzed para distinguir ambos casos.
    abuseipdb: Optional[AbuseIpInfo] = None
    risk_score: Optional[int] = None  # se rellena con la reputación de IP, o con el análisis completo si lo hay
    risk_flags: list[RiskFlag] = []
    fully_analyzed: bool = False  # True solo si tuvo WHOIS/SSL/VirusTotal completo (las primeras max_full_analysis)


class TyposquattingResponse(BaseModel):
    domain: str
    analyzed_at: datetime
    variants_generated: int
    resolved_count: int
    candidates: list[TyposquattingCandidate] = []  # solo las que resuelven (las que no, no aportan nada)
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []


class TyposquattingCaseResponse(TyposquattingResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TyposquattingCaseListItem(BaseModel):
    id: int
    domain: str
    resolved_count: int
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
