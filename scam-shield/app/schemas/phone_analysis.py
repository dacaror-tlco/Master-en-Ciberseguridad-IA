from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import RiskFlag


class PhoneAnalysisRequest(BaseModel):
    phone: str = Field(
        ...,
        description="Número de teléfono. Mejor en formato internacional (+34600123456); si no, se asume default_region.",
        examples=["+34600123456"],
    )
    default_region: str = Field(
        "ES",
        description="Región asumida si el número no viene en formato internacional (código ISO de 2 letras)",
    )


class PhoneInfo(BaseModel):
    e164: str
    international_format: str
    national_format: str
    country_code: int
    country_name: Optional[str] = None
    region_description: Optional[str] = None
    carrier: Optional[str] = None
    line_type: str  # MOBILE | FIXED_LINE | VOIP | PREMIUM_RATE | TOLL_FREE | UNKNOWN | ...
    is_valid: bool
    is_possible: bool
    timezones: list[str] = []


class CommunityReportInfo(BaseModel):
    """
    Reportes de OTRAS PERSONAS sobre este número (spam/fraude/telemarketing),
    no la identidad de quien lo tiene. Ver openspam_service.py para el porqué
    de esta distinción.
    """
    reports_count: int = 0
    category: Optional[str] = None       # ej: "fraude", "telemarketing", "publicidad"
    province: Optional[str] = None
    danger_level: Optional[str] = None   # ej: "alto", "medio", "bajo"


class FraudScoreInfo(BaseModel):
    """
    Señales de comportamiento/reputación de IPQualityScore. Su API TAMBIÉN
    devuelve un campo `name` con el nombre del titular o de la empresa
    asociada al número (misma limitación que Truecaller) — a propósito NO
    se lee ni se expone ese campo aquí, ver ipqualityscore_service.py.
    """
    fraud_score: Optional[int] = None
    voip: bool = False
    prepaid: bool = False
    recent_abuse: bool = False
    leaked: bool = False
    spammer: bool = False
    active: Optional[bool] = None
    line_type: Optional[str] = None
    carrier: Optional[str] = None


class CarrierIntelligenceInfo(BaseModel):
    """
    Carrier/tipo de línea EN TIEMPO REAL vía Twilio Lookup (add-on
    line_type_intelligence) — a diferencia de PhoneInfo.line_type (offline,
    por rango estático de numeración), esto detecta portabilidad y VoIP
    moderno no catalogado. A propósito NO se piden los add-ons caller_name
    (CNAM) ni identity_match de Twilio: esos sí revelan/verifican identidad.
    """
    carrier_name: Optional[str] = None
    line_type: Optional[str] = None
    mobile_country_code: Optional[str] = None
    mobile_network_code: Optional[str] = None


class PhoneAnalysisResponse(BaseModel):
    phone: Optional[PhoneInfo] = None
    community_reports: Optional[CommunityReportInfo] = None
    fraud_score: Optional[FraudScoreInfo] = None
    carrier_intelligence: Optional[CarrierIntelligenceInfo] = None
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime


class PhoneCaseResponse(PhoneAnalysisResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PhoneCaseListItem(BaseModel):
    id: int
    raw_phone: str
    line_type: Optional[str] = None
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
