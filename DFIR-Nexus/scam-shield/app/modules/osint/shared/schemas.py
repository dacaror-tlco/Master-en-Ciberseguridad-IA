"""
Vocabulario de schemas compartido entre TODOS los sub-módulos de OSINT
(dominio, email, wallet, typosquatting, teléfono, CNMV, imagen, IP).

Extraído de lo que antes era app/schemas/domain_analysis.py: RiskFlag y
AbuseIpInfo en particular se importan literalmente desde casi cada
sub-módulo (motores de riesgo, análisis de email/typosquatting/IP...), así
que viven aquí en vez de en domain/schemas.py para no forzar que cada
sub-módulo dependa del sub-módulo "domain".
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RiskFlag(BaseModel):
    """Cada señal de riesgo detectada, con su propio peso y explicación."""
    code: str
    description: str
    severity: str  # "low" | "medium" | "high"


class WhoisInfo(BaseModel):
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    domain_age_days: Optional[int] = None
    country: Optional[str] = None
    name_servers: list[str] = []


class AbuseIpInfo(BaseModel):
    """
    Reputación de una IP según AbuseIPDB (https://www.abuseipdb.com):
    consenso de la comunidad de seguridad sobre esa dirección (fuerza
    bruta, escaneos, spam, phishing...), NO identidad de ninguna persona.
    Se usa desde dominio, email (IP de origen) e IP directamente —
    `shared/ip_risk_engine.py` es la única fuente de verdad de scoring
    para las tres.
    """
    ip_address: str
    abuse_confidence_score: int = 0
    total_reports: int = 0
    is_whitelisted: Optional[bool] = None
    is_tor: bool = False
    usage_type: Optional[str] = None
    isp: Optional[str] = None
    domain: Optional[str] = None
    country_code: Optional[str] = None
    last_reported_at: Optional[datetime] = None


class IpReputationEntry(BaseModel):
    """Reputación (AbuseIPDB) de una de las IPs a las que resuelve un dominio."""
    ip: str
    abuseipdb: Optional[AbuseIpInfo] = None
