"""
Servicio de consulta al CDX API de Wayback Machine / Internet Archive
(https://web.archive.org/cdx): historial de capturas archivadas de un
dominio. Gratis, sin API key.

Interesa por dos motivos:
1. Cero capturas = el dominio nunca ha sido indexado. Normal en uno
   recién creado, pero combinado con otras señales (WHOIS reciente, SSL
   recién emitido) refuerza "recién montado para esta campaña".
2. Una primera captura muy anterior a la fecha de registro WHOIS actual
   es la señal fuerte: el dominio existió antes con otro contenido y fue
   "recuperado" tras expirar (domain drop-catching), técnica habitual
   para heredar la reputación/backlinks de un dominio ajeno. Esa
   comparación la hace el risk_engine, aquí solo se aportan los datos.

El conteo total se limita a `_COUNT_CAP` capturas: para un dominio
enorme (con cientos de miles de capturas) descargar el listado completo
solo para contar sería lento y no aporta más señal que "muchísimas".
"""
from datetime import datetime, timezone

import requests

from app.schemas.domain_analysis import WaybackInfo

_CDX_URL = "https://web.archive.org/cdx/search/cdx"
_COUNT_CAP = 1000


def _parse_timestamp(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def _first_data_row(rows: list) -> list | None:
    """El CDX API devuelve la fila de cabecera (nombres de columna) primero; sin capturas, solo llega esa fila (o ninguna)."""
    return rows[1] if len(rows) > 1 else None


def get_wayback_info(domain: str, timeout: float = 15.0) -> WaybackInfo:
    # Una sola petición cubre "primera captura" Y "conteo": en orden ascendente
    # (el orden por defecto), la fila 1 ES la primera captura, y el nº de filas
    # devueltas (hasta el tope) ES el conteo. Solo hace falta una segunda
    # petición aparte para la ÚLTIMA captura (limit negativo = últimas N filas,
    # documentado en el CDX API — no hay forma de pedir "primera + última + conteo" en una sola).
    first_and_count_resp = requests.get(
        _CDX_URL, params={"url": domain, "output": "json", "fl": "timestamp", "limit": _COUNT_CAP}, timeout=timeout,
    )
    first_and_count_resp.raise_for_status()
    rows = first_and_count_resp.json() or []
    first_row = _first_data_row(rows)

    if first_row is None:
        return WaybackInfo(total_snapshots=0, first_snapshot=None, last_snapshot=None)

    first_snapshot = _parse_timestamp(first_row[0])
    total_snapshots = len(rows) - 1

    last_resp = requests.get(
        _CDX_URL, params={"url": domain, "output": "json", "fl": "timestamp", "limit": -1}, timeout=timeout,
    )
    last_resp.raise_for_status()
    last_row = _first_data_row(last_resp.json() or [])
    last_snapshot = _parse_timestamp(last_row[0]) if last_row else first_snapshot

    return WaybackInfo(
        total_snapshots=total_snapshots,
        first_snapshot=first_snapshot,
        last_snapshot=last_snapshot,
    )
