"""
Servicio de consulta WHOIS.

Aísla la librería externa (python-whois) detrás de una función propia.
Así, si mañana cambiamos de librería o pasamos a consultar RDAP directamente,
solo tocamos este archivo.
"""
from datetime import datetime, timezone

import whois as whois_lib

from app.schemas.domain_analysis import WhoisInfo


def _first_or_none(value):
    """python-whois a veces devuelve una lista de fechas/registrars en vez de un único valor."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def get_whois_info(domain: str) -> WhoisInfo:
    raw = whois_lib.whois(domain)

    creation_date = _first_or_none(raw.creation_date)
    domain_age_days = None
    if creation_date:
        if creation_date.tzinfo is None:
            creation_date = creation_date.replace(tzinfo=timezone.utc)
        domain_age_days = (datetime.now(timezone.utc) - creation_date).days

    return WhoisInfo(
        registrar=raw.registrar,
        creation_date=creation_date,
        expiration_date=_first_or_none(raw.expiration_date),
        domain_age_days=domain_age_days,
        country=raw.country,
        name_servers=raw.name_servers or [],
    )
