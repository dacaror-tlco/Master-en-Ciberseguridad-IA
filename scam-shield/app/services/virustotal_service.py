"""
Servicio de consulta a VirusTotal.

Complementa al WHOIS/SSL con el veredicto de decenas de motores antivirus
y de reputación (Google Safe Browsing, Sophos, Kaspersky...) sobre un
dominio. Son señales complementarias, no redundantes: WHOIS/SSL miran
"cómo se construyó" el dominio (edad, certificado), VirusTotal mira "qué
opina de él la comunidad de seguridad" en base a detecciones reales.
"""
import requests

from app.core.config import settings
from app.schemas.domain_analysis import VirusTotalInfo

_VT_DOMAIN_URL = "https://www.virustotal.com/api/v3/domains"


def get_virustotal_info(domain: str) -> VirusTotalInfo:
    if not settings.virustotal_api_key:
        raise RuntimeError(
            "No hay VIRUSTOTAL_API_KEY configurada. Consigue una gratuita en "
            "https://www.virustotal.com/gui/join-us y añádela a tu archivo .env"
        )

    resp = requests.get(
        f"{_VT_DOMAIN_URL}/{domain}",
        headers={"x-apikey": settings.virustotal_api_key},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    attrs = (data.get("data") or {}).get("attributes") or {}
    stats = attrs.get("last_analysis_stats") or {}
    categories = attrs.get("categories") or {}

    return VirusTotalInfo(
        malicious_count=stats.get("malicious", 0),
        suspicious_count=stats.get("suspicious", 0),
        harmless_count=stats.get("harmless", 0),
        undetected_count=stats.get("undetected", 0),
        reputation=attrs.get("reputation", 0),
        categories=sorted(set(categories.values())),
    )
