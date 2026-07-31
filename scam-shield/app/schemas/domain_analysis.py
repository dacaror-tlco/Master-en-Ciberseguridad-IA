"""
Esquemas de entrada/salida para el análisis de dominios.
Separar esto del modelo de base de datos nos da libertad para cambiar
la forma de la API sin tocar cómo guardamos los datos, y viceversa.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DomainAnalysisRequest(BaseModel):
    domain: str = Field(..., description="Dominio a analizar, sin http:// ni www.", examples=["ejemplo-sospechoso.com"])


class WhoisInfo(BaseModel):
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    domain_age_days: Optional[int] = None
    country: Optional[str] = None
    name_servers: list[str] = []


class SSLCertInfo(BaseModel):
    has_valid_cert: bool = False
    issuer: Optional[str] = None
    issued_date: Optional[datetime] = None
    days_since_issued: Optional[int] = None
    subject_alt_names: list[str] = []


class VirusTotalInfo(BaseModel):
    """
    Veredicto de la comunidad de seguridad sobre el dominio (decenas de
    motores antivirus y de reputación: Google Safe Browsing, Sophos,
    Kaspersky...). Complementa al WHOIS/SSL: estos miran "cómo se
    construyó" el dominio, VirusTotal mira "qué opina de él la comunidad".
    """
    malicious_count: int = 0
    suspicious_count: int = 0
    harmless_count: int = 0
    undetected_count: int = 0
    reputation: int = 0
    categories: list[str] = []


class RiskFlag(BaseModel):
    """Cada señal de riesgo detectada, con su propio peso y explicación."""
    code: str
    description: str
    severity: str  # "low" | "medium" | "high"


class DnsRecords(BaseModel):
    """
    Configuración DNS completa del dominio, más allá de la única IP que
    devuelve una resolución simple: todas las IPs (A), a través de qué
    proveedor recibe correo (MX) y si protege su propio dominio contra
    suplantación (SPF/DMARC en TXT) y sus certificados (CAA).
    """
    all_ips: list[str] = []
    mx_hosts: list[str] = []
    txt_records: list[str] = []
    has_spf: bool = False
    has_dmarc: bool = False
    caa_records: list[str] = []


class CrtShInfo(BaseModel):
    """
    Subdominios descubiertos vía Certificate Transparency (crt.sh): cada
    certificado emitido para cualquier subdominio queda públicamente
    registrado ahí, independientemente de si el subdominio está listado en
    algún sitio. Revela infraestructura relacionada (paneles de login,
    subdominios de prueba) que WHOIS/DNS del dominio principal no muestran.
    """
    subdomain_count: int = 0
    subdomains: list[str] = []
    suspected_brand_subdomains: list[str] = Field(
        default=[], description="Subdominios cuyo nombre menciona una marca conocida sin pertenecerle (ver brand_dictionary)"
    )


class WaybackInfo(BaseModel):
    """
    Historial en Internet Archive (Wayback Machine): cuántas veces se ha
    archivado este dominio y desde cuándo. Sin snapshots = dominio nunca
    indexado (normal en uno recién creado, pero combinado con otras
    señales refuerza "recién montado"). Un primer snapshot MUY anterior a
    la fecha de registro WHOIS actual es la señal fuerte: el dominio existió
    antes con otro dueño/contenido y fue re-registrado tras expirar
    ("domain drop-catching"), técnica habitual para heredar reputación.
    """
    total_snapshots: int = 0
    first_snapshot: Optional[datetime] = None
    last_snapshot: Optional[datetime] = None


class AbuseIpInfo(BaseModel):
    """
    Reputación de una IP según AbuseIPDB (https://www.abuseipdb.com):
    consenso de la comunidad de seguridad sobre esa dirección (fuerza
    bruta, escaneos, spam, phishing...), NO identidad de ninguna persona
    — mismo principio que VirusTotal para dominios. Se usa tanto desde el
    módulo de dominio (IP a la que resuelve) como desde el módulo de IP
    (`ip_risk_engine.py` es la única fuente de verdad para ambos).
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
    """Reputación (AbuseIPDB) de una de las IPs a las que resuelve el dominio."""
    ip: str
    abuseipdb: Optional[AbuseIpInfo] = None


class DomainAnalysisResponse(BaseModel):
    domain: str
    analyzed_at: datetime
    whois: Optional[WhoisInfo] = None
    ssl: Optional[SSLCertInfo] = None
    virustotal: Optional[VirusTotalInfo] = None
    resolved_ip: Optional[str] = None
    abuseipdb: Optional[AbuseIpInfo] = None
    dns: Optional[DnsRecords] = Field(
        None, description="Registros DNS completos (todas las IPs, MX, TXT/SPF/DMARC, CAA), más allá de la IP principal"
    )
    ip_reputations: list[IpReputationEntry] = Field(
        default=[], description="Reputación AbuseIPDB de cada IP en dns.all_ips (incluida la principal, ya en 'abuseipdb')"
    )
    crtsh: Optional[CrtShInfo] = Field(None, description="Subdominios y certificados relacionados (Certificate Transparency)")
    wayback: Optional[WaybackInfo] = Field(None, description="Historial en Internet Archive / Wayback Machine")
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100, description="0 = sin riesgo aparente, 100 = riesgo máximo")
    errors: list[str] = []  # si alguna fuente falla, lo registramos sin tumbar toda la respuesta


class CaseResponse(DomainAnalysisResponse):
    """Igual que DomainAnalysisResponse, pero ya persistido: incluye el id con el que consultarlo luego."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # permite construir esto directamente desde el modelo SQLAlchemy


class CaseListItem(BaseModel):
    """Versión ligera para listados: sin todo el detalle de WHOIS/SSL, solo lo esencial."""
    id: int
    domain: str
    risk_score: int
    analyzed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
