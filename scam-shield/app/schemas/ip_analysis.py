from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import AbuseIpInfo, RiskFlag


class IpAnalysisRequest(BaseModel):
    ip: str = Field(..., description="Dirección IPv4 o IPv6 a analizar", examples=["1.2.3.4"])


class IpAnalysisResponse(BaseModel):
    ip: str
    abuseipdb: Optional[AbuseIpInfo] = None
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime


class IpCaseResponse(IpAnalysisResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class IpCaseListItem(BaseModel):
    id: int
    ip: str
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
