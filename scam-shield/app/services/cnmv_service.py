"""
Servicio de consulta al listado de "entidades advertidas" de la CNMV
(chiringuitos financieros): https://www.cnmv.es/Portal/BusquedaAdvertencias.aspx

La CNMV NO ofrece una API — es un listado HTML público de cientos de
páginas, paginado por querystring (`?tipo=1&page=N`, confirmado real y
estable, sin necesidad de sesión ni tokens). No hay endpoint de búsqueda
por nombre confirmado, así que scrapeamos las páginas más recientes y
buscamos localmente (ver api/routes/cnmv.py para la lógica de caché).

AVISO IMPORTANTE: este scraper se escribió sin poder inspeccionar el HTML
en crudo de la página (la herramienta usada para verificarla la convierte
a texto/markdown, no deja ver las etiquetas exactas). La estructura de la
tabla se infiere de forma defensiva — buscando la tabla cuya cabecera
contiene "Fecha" y "Compañías" en vez de depender de un id o clase CSS
concretos — pero **no está garantizado que funcione a la primera**. Si
falla, lo más probable es que la CNMV haya cambiado el HTML de la tabla;
revisa `_parse_page()` con una copia real del HTML (`curl` o "ver código
fuente" del navegador) antes de tocar nada más.
"""
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.cnmv_warning import CnmvWarning

_LIST_URL = "https://www.cnmv.es/portal/resultadobusqueda.aspx"
_FECHA_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_CACHE_MAX_AGE_HOURS = 24
_DEFAULT_MAX_PAGES = 50


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    target_table = None
    for table in soup.find_all("table"):
        header_text = table.get_text(" ", strip=True)[:800].lower()
        if "fecha" in header_text and "compañ" in header_text:
            target_table = table
            break

    if target_table is None:
        raise RuntimeError(
            "No se encontró la tabla de advertencias en la página de la CNMV — "
            "es posible que hayan cambiado la estructura de su web (ver el aviso "
            "en la cabecera de cnmv_service.py)."
        )

    entries = []
    for row in target_table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        fecha = cells[0].get_text(strip=True)
        # Una fila de datos real siempre empieza con una fecha dd/mm/aaaa.
        # Si no, es la cabecera, un separador, o algo que no es un dato -> se ignora.
        if not _FECHA_PATTERN.match(fecha):
            continue

        companias = cells[1].get_text("\n", strip=True)
        observaciones = cells[-1].get_text(strip=True) if len(cells) >= 5 else None

        entries.append({"fecha": fecha, "companias": companias, "observaciones": observaciones or None})

    return entries


def fetch_page(page: int, timeout: float = 15.0) -> list[dict]:
    """
    Descarga y parsea una página del listado (0-indexado, como usa la
    propia CNMV en su paginación). Devuelve una lista vacía si la página
    no tiene resultados (fin del listado).
    """
    resp = requests.get(
        _LIST_URL,
        params={"lang": "es", "tipo": 1, "page": page},
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ScamShield/1.0; +investigacion academica)"},
    )
    resp.raise_for_status()
    return _parse_page(resp.text)


def fetch_recent(max_pages: int = 50) -> list[dict]:
    """
    Descarga las `max_pages` páginas más recientes (la CNMV las lista de
    más nueva a más antigua). Con ~10 entradas/página, 50 páginas cubren
    del orden de un año largo de advertencias — suficiente para detectar
    campañas activas, aunque no todo el histórico desde que existe el
    registro (miles de entidades desde hace años).
    """
    all_entries: list[dict] = []
    for page in range(max_pages):
        entries = fetch_page(page)
        if not entries:
            break
        all_entries.extend(entries)
    return all_entries


def ensure_cache_fresh(db: Session, max_pages: int = _DEFAULT_MAX_PAGES) -> list[str]:
    """
    Refresca la caché local si está vacía o caducada (>24h). Devuelve una
    lista de avisos/errores (vacía si todo fue bien o si no hacía falta
    refrescar). Si el refresco falla, se mantiene la caché anterior en vez
    de dejar la búsqueda sin ningún dato.
    """
    newest = db.query(CnmvWarning).order_by(desc(CnmvWarning.scraped_at)).first()
    if newest is None:
        is_stale = True
    else:
        # SQLite no conserva la zona horaria al guardar DateTime(timezone=True):
        # al releerlo puede venir "naive". Lo normalizamos a UTC antes de restar,
        # o la resta entre un datetime "aware" y uno "naive" lanza TypeError.
        newest_scraped_at = newest.scraped_at
        if newest_scraped_at.tzinfo is None:
            newest_scraped_at = newest_scraped_at.replace(tzinfo=timezone.utc)
        is_stale = (datetime.now(timezone.utc) - newest_scraped_at) > timedelta(hours=_CACHE_MAX_AGE_HOURS)
    if not is_stale:
        return []

    try:
        entries = fetch_recent(max_pages=max_pages)
    except Exception as exc:
        return [f"No se pudo refrescar la caché de advertencias de la CNMV: {exc}"]

    if not entries:
        return ["La CNMV no devolvió ninguna advertencia al refrescar la caché (o cambió el formato de su web)"]

    now = datetime.now(timezone.utc)
    db.query(CnmvWarning).delete()
    for e in entries:
        db.add(CnmvWarning(fecha=e["fecha"], companias=e["companias"], observaciones=e.get("observaciones"), scraped_at=now))
    db.commit()
    return []
