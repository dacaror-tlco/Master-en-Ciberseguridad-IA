"""
Servicio de consulta a crt.sh (https://crt.sh): buscador público de
Certificate Transparency, el registro donde TODAS las autoridades
certificadoras (Let's Encrypt, DigiCert...) publican cada certificado
que emiten, por ley desde 2018. Consultando por dominio se obtienen
todos los subdominios para los que se ha emitido un certificado alguna
vez — infraestructura relacionada (paneles de login, entornos de
prueba) que ni WHOIS ni una resolución DNS del dominio principal
revelan. Gratis, sin API key, sin límite documentado de uso razonable.

Nota: crt.sh es un servicio público conocido por ser inestable bajo carga
(devuelve 404/502 de forma intermitente incluso para consultas válidas,
sobre todo en dominios con muchos certificados). No es un fallo de este
código — por eso quien llama a `get_crtsh_info` debe tratarlo igual que
WHOIS/VirusTotal: opcional, con su propio try/except que degrada sin
tumbar el resto del análisis.
"""
import requests

from app.schemas.domain_analysis import CrtShInfo
from app.services import brand_dictionary

_CRTSH_URL = "https://crt.sh/"
_MAX_SUBDOMAINS_RETURNED = 50


def get_crtsh_info(domain: str, timeout: float = 20.0) -> CrtShInfo:
    resp = requests.get(
        _CRTSH_URL,
        params={"q": domain, "output": "json"},
        headers={"User-Agent": "ScamShield/1.0"},
        timeout=timeout,
    )
    resp.raise_for_status()
    entries = resp.json() or []

    subdomains: set[str] = set()
    for entry in entries:
        for name in (entry.get("name_value") or "").split("\n"):
            name = name.strip().lower().lstrip("*.")
            if name and (name == domain or name.endswith("." + domain)):
                subdomains.add(name)
    subdomains.discard(domain)  # el propio dominio no es un "subdominio relacionado"

    suspected_brand_subdomains = sorted(
        sub for sub in subdomains if brand_dictionary.closest_brand(sub)
    )

    sorted_subdomains = sorted(subdomains)
    return CrtShInfo(
        subdomain_count=len(sorted_subdomains),
        subdomains=sorted_subdomains[:_MAX_SUBDOMAINS_RETURNED],
        suspected_brand_subdomains=suspected_brand_subdomains,
    )
