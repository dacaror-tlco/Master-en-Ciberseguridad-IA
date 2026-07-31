"""
Enriquecimiento de los enlaces encontrados en el cuerpo de un email.

Deliberadamente separado de `email_risk_engine.py`: aquí solo se produce
información (EmailLinkInfo), igual que `whois_service`/`virustotal_service`
producen datos para el módulo de dominio — quien decide qué es "señal de
riesgo" y cuántos puntos vale es siempre el risk_engine correspondiente.

Un email de phishing puede traer decenas de enlaces (imágenes de
seguimiento, botones repetidos con la misma URL, redes sociales del pie de
firma...). Consultar WHOIS/VirusTotal para cada uno, de forma síncrona
dentro de una sola petición HTTP, sería lento y además agotaría en
segundos el límite gratuito de VirusTotal (~4 consultas/minuto). Por eso:

- Se ignoran los dominios de infraestructura habitual (Google, Microsoft,
  redes sociales, proveedores de email marketing) que aparecen en
  cualquier newsletter legítima y no aportan señal.
- Solo se consulta WHOIS/VirusTotal para como mucho `_MAX_DOMAINS_CHECKED`
  dominios distintos por email, priorizando los primeros que aparecen.
"""
import re

from app.schemas.email_analysis import EmailLinkInfo
from app.services import brand_dictionary, virustotal_service, whois_service
from app.services.domain_utils import normalize_domain

_URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly",
    "cutt.ly", "rebrand.ly", "shorturl.at", "buff.ly", "rb.gy", "s.id",
}

_TRUSTED_INFRA = {
    "google.com", "gmail.com", "youtube.com", "outlook.com", "live.com",
    "microsoft.com", "apple.com", "icloud.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "linkedin.com", "whatsapp.com",
    "list-manage.com", "mailchimp.com", "sendgrid.net", "constantcontact.com",
    "hubspotlinks.com", "click.email",
}

_MAX_DOMAINS_CHECKED = 5


def _domain_of(url: str) -> str | None:
    match = re.match(r"^https?://([^/]+)", url.strip(), re.IGNORECASE)
    if not match:
        return None
    host = match.group(1).split("@")[-1].split(":")[0]  # descarta user:pass@ y :puerto
    if not host:
        return None
    return normalize_domain(host)


def _resolve_shortener(url: str) -> str | None:
    import requests  # import perezoso: solo hace falta si hay acortadores

    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        return _domain_of(resp.url)
    except Exception:
        return None


def analyze_links(urls: list[str]) -> list[EmailLinkInfo]:
    results: list[EmailLinkInfo] = []
    checked_count = 0

    for url in urls:
        domain = _domain_of(url)
        if not domain:
            continue

        is_shortener = domain in _URL_SHORTENERS
        redirects_to = _resolve_shortener(url) if is_shortener else None
        effective_domain = redirects_to or domain

        link_info = EmailLinkInfo(
            url=url,
            domain=domain,
            is_shortener=is_shortener,
            redirects_to=redirects_to,
            suspected_brand=brand_dictionary.closest_brand(effective_domain),
        )

        if effective_domain not in _TRUSTED_INFRA and checked_count < _MAX_DOMAINS_CHECKED:
            checked_count += 1
            link_info.checked = True

            try:
                whois_info = whois_service.get_whois_info(effective_domain)
                link_info.domain_age_days = whois_info.domain_age_days
            except Exception:
                pass

            try:
                vt_info = virustotal_service.get_virustotal_info(effective_domain)
                link_info.virustotal_malicious_count = vt_info.malicious_count
            except Exception:
                pass

        results.append(link_info)

    return results
