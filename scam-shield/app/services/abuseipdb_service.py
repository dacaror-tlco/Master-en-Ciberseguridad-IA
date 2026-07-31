"""
Servicio de consulta a AbuseIPDB (https://www.abuseipdb.com):
reputación de una IP según reportes de la comunidad de seguridad (fuerza
bruta, escaneos, spam, phishing...) — mismo principio que VirusTotal para
dominios: consenso de reputación de infraestructura, no vigilancia de
personas. Lo usan tanto el módulo de dominio (IP a la que resuelve) como
el módulo de IP (`app/services/ip_analysis_service.py`).

Endpoint confirmado contra la documentación oficial
(https://docs.abuseipdb.com/#check-endpoint): GET /api/v2/check, auth por
header `Key` (no query param, no Bearer). Tier gratuito: 1000
peticiones/día.
"""
import requests

from app.core.config import settings
from app.schemas.domain_analysis import AbuseIpInfo

_ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"


def get_ip_reputation(ip: str) -> AbuseIpInfo:
    if not settings.abuseipdb_api_key:
        raise RuntimeError(
            "No hay ABUSEIPDB_API_KEY configurada. Consigue una gratuita en "
            "https://www.abuseipdb.com/register y añádela a tu archivo .env"
        )

    resp = requests.get(
        _ABUSEIPDB_URL,
        headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
        params={"ipAddress": ip},
        timeout=10,
    )
    resp.raise_for_status()
    data = (resp.json() or {}).get("data") or {}

    return AbuseIpInfo(
        ip_address=data.get("ipAddress", ip),
        abuse_confidence_score=data.get("abuseConfidenceScore", 0),
        total_reports=data.get("totalReports", 0),
        is_whitelisted=data.get("isWhitelisted"),
        is_tor=bool(data.get("isTor", False)),
        usage_type=data.get("usageType"),
        isp=data.get("isp"),
        domain=data.get("domain"),
        country_code=data.get("countryCode"),
        last_reported_at=data.get("lastReportedAt"),
    )
