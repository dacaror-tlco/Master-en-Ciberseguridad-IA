"""
Schemas de entrada/salida para el análisis forense de cabeceras de email.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.domain_analysis import AbuseIpInfo, RiskFlag, WhoisInfo


class EmailAnalysisRequest(BaseModel):
    raw_email: str = Field(
        ...,
        description=(
            "Idealmente el email completo en formato 'fuente original' (raw/source): "
            "en Gmail, menú de 3 puntos -> 'Mostrar original' -> copiar todo el contenido; "
            "en Outlook, Archivo -> Propiedades -> 'Encabezados de Internet'. "
            "Si no se dispone de eso, también se acepta pegar el texto visible del email "
            "(remitente, asunto, cuerpo) tal cual: el análisis degrada con gracia, indicando "
            "en 'is_raw_source' que no se pudieron verificar SPF/DKIM/DMARC, pero sigue "
            "analizando enlaces, adjuntos y el nombre del remitente."
        ),
    )


class EmailHeaderInfo(BaseModel):
    from_address: Optional[str] = None
    from_display_name: Optional[str] = None
    reply_to: Optional[str] = None
    return_path: Optional[str] = None
    subject: Optional[str] = None
    date: Optional[datetime] = None

    spf_result: Optional[str] = None   # pass | fail | softfail | neutral | none
    dkim_result: Optional[str] = None  # pass | fail | none
    dmarc_result: Optional[str] = None  # pass | fail | none

    originating_ip: Optional[str] = None
    received_hop_count: int = 0


class EmailLinkInfo(BaseModel):
    """Un enlace encontrado en el cuerpo del email, con la información con la que se ha podido enriquecer."""
    url: str
    domain: Optional[str] = None
    is_shortener: bool = False
    redirects_to: Optional[str] = Field(
        None, description="Dominio de destino real, si el enlace es un acortador y se pudo resolver"
    )
    suspected_brand: Optional[str] = Field(
        None, description="Marca conocida a la que este dominio parece imitar, sin serlo (ver brand_dictionary)"
    )
    domain_age_days: Optional[int] = None
    virustotal_malicious_count: Optional[int] = None
    checked: bool = Field(False, description="Si se llegó a consultar WHOIS/VirusTotal para este dominio (acotado a un máximo por email)")


class EmailAttachmentInfo(BaseModel):
    """Un adjunto del email. No se guarda el contenido, solo su huella y metadatos."""
    filename: str
    extension: Optional[str] = None
    size_bytes: int
    sha256: str
    is_dangerous_extension: bool = False
    has_double_extension: bool = False


class EmailAnalysisResponse(BaseModel):
    headers: EmailHeaderInfo
    sender_domain_whois: Optional[WhoisInfo] = None
    originating_ip_abuseipdb: Optional[AbuseIpInfo] = Field(
        None, description="Reputación (AbuseIPDB) de la IP de origen extraída de la cabecera Received, si se pudo consultar"
    )
    links: list[EmailLinkInfo] = []
    attachments: list[EmailAttachmentInfo] = []
    is_raw_source: bool = Field(
        True, description="Si el texto proporcionado era el código fuente real del email (con cabeceras técnicas) o solo el texto visible pegado por la víctima"
    )
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime
    raw_email_sha256: Optional[str] = Field(
        None, description="Huella SHA-256 del email original en el momento de la captura (informativa, no se guarda el contenido)"
    )
    ai_explanation: Optional[str] = Field(
        None, description="Explicación en lenguaje sencillo generada por IA (solo si hay ANTHROPIC_API_KEY configurada)"
    )

    # `links`/`attachments`/`is_raw_source` se guardan en columnas nullable
    # (se añadieron después de los campos originales, ver models/email_case.py),
    # así que un caso analizado ANTES de que existieran estas columnas trae
    # `None` desde la base de datos. Normalizamos aquí a los valores que ya
    # tendría un caso analizado con la lógica actual (sin enlaces/adjuntos
    # detectados, is_raw_source desconocido -> se asume True, el
    # comportamiento previo a este cambio), para que el endpoint no rompa
    # con un 500 al consultar un caso antiguo.
    @field_validator("links", "attachments", mode="before")
    @classmethod
    def _default_empty_list(cls, v):
        return v if v is not None else []

    @field_validator("is_raw_source", mode="before")
    @classmethod
    def _default_is_raw_source(cls, v):
        return v if v is not None else True


class EmailCaseResponse(EmailAnalysisResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmailCaseListItem(BaseModel):
    id: int
    from_address: Optional[str] = None
    subject: Optional[str] = None
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
