"""
Cruce contra la lista de direcciones cripto sancionadas por la OFAC
(Office of Foreign Assets Control, Tesoro de EEUU) — asociadas a
ransomware, exchanges sancionados u otros delitos graves.

Fuente: espejo público `0xB10C/ofac-sanctioned-digital-currency-addresses`
(rama `lists`), que extrae y regenera cada noche (GitHub Actions) las
direcciones cripto del listado SDN oficial de la OFAC, en ficheros de
texto plano (una dirección por línea) — confirmado en vivo antes de
implementar esto. Mismo patrón de caché perezosa que `cnmv_service.py`:
se refresca sola si tiene más de 24h, y si el refresco falla se sigue
usando la copia anterior en vez de dejar el cruce sin ningún dato.
"""
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.ofac_sanctioned_address import OfacSanctionedAddress

_BASE_URL = "https://raw.githubusercontent.com/0xB10C/ofac-sanctioned-digital-currency-addresses/lists/"
_LISTS = {
    "BTC": "sanctioned_addresses_XBT.txt",
    "ETH": "sanctioned_addresses_ETH.txt",
    "TRON": "sanctioned_addresses_TRX.txt",
}
_CACHE_MAX_AGE_HOURS = 24


def _fetch_list(asset: str, timeout: float = 15.0) -> list[str]:
    resp = requests.get(_BASE_URL + _LISTS[asset], timeout=timeout)
    resp.raise_for_status()
    return [line.strip() for line in resp.text.splitlines() if line.strip()]


def ensure_cache_fresh(db: Session) -> list[str]:
    """
    Refresca la caché local si está vacía o caducada (>24h). Devuelve una
    lista de avisos/errores (vacía si todo fue bien o si no hacía falta
    refrescar). Si el refresco falla, se mantiene la caché anterior.
    """
    newest = db.query(OfacSanctionedAddress).order_by(desc(OfacSanctionedAddress.cached_at)).first()
    if newest is None:
        is_stale = True
    else:
        cached_at = newest.cached_at
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        is_stale = (datetime.now(timezone.utc) - cached_at) > timedelta(hours=_CACHE_MAX_AGE_HOURS)
    if not is_stale:
        return []

    errors = []
    fetched: dict[str, list[str]] = {}
    for asset in _LISTS:
        try:
            fetched[asset] = _fetch_list(asset)
        except Exception as exc:
            errors.append(f"No se pudo refrescar la lista OFAC de {asset}: {exc}")

    if not fetched:
        return errors  # ningún fichero se pudo descargar, se conserva la caché anterior tal cual

    now = datetime.now(timezone.utc)
    # Solo se reemplazan las listas que sí se han podido descargar — si p.ej.
    # falla solo la de Tron, no se borra su caché anterior (mejor una lista
    # algo desactualizada que ninguna).
    for asset, addresses in fetched.items():
        db.query(OfacSanctionedAddress).filter(OfacSanctionedAddress.asset == asset).delete()
        for address in addresses:
            db.add(OfacSanctionedAddress(address=address, asset=asset, cached_at=now))
    db.commit()
    return errors


def is_sanctioned(db: Session, address: str, chain: str) -> bool:
    match = (
        db.query(OfacSanctionedAddress)
        .filter(OfacSanctionedAddress.asset == chain, OfacSanctionedAddress.address == address)
        .first()
    )
    return match is not None
