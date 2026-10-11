"""
Caché efímera, solo en memoria del proceso, de los bytes originales de una
imagen ya analizada.

`ImageCase` nunca guarda el archivo en sí (solo hash perceptual + SHA-256),
a propósito (ver `app/models/image_case.py`). Para poder ofrecer búsqueda
inversa (SerpApi) y búsqueda facial (PimEyes) como acciones opcionales
posteriores sin pedirle al usuario que resuba la foto, se guarda aquí un
rato — nunca en disco ni en la base de datos, y con TTL corto — keyed por
el id del caso.

También vive aquí el mecanismo de "token de previsualización": un enlace
público, opaco y de un solo uso que permite a SerpApi descargar la imagen
para completar la búsqueda inversa (ver `serpapi_service.py` — Google no
acepta subida directa de bytes, solo una URL pública).
"""
import secrets
import threading
from datetime import datetime, timedelta, timezone

_CASE_TTL = timedelta(minutes=15)
_PREVIEW_TTL = timedelta(minutes=5)

_lock = threading.Lock()
_by_case_id: dict[int, tuple[bytes, datetime]] = {}
_preview_tokens: dict[str, tuple[bytes, datetime]] = {}


def put(case_id: int, raw_bytes: bytes) -> None:
    with _lock:
        _by_case_id[case_id] = (raw_bytes, datetime.now(timezone.utc) + _CASE_TTL)


def get(case_id: int) -> bytes | None:
    with _lock:
        entry = _by_case_id.get(case_id)
        if entry is None:
            return None
        raw_bytes, expires_at = entry
        if datetime.now(timezone.utc) > expires_at:
            del _by_case_id[case_id]
            return None
        return raw_bytes


def create_preview_token(raw_bytes: bytes) -> str:
    """Token opaco de un solo uso para exponer temporalmente la imagen en una URL pública."""
    token = secrets.token_urlsafe(32)
    with _lock:
        _preview_tokens[token] = (raw_bytes, datetime.now(timezone.utc) + _PREVIEW_TTL)
    return token


def consume_preview_token(token: str) -> bytes | None:
    """Sirve la imagen una única vez: se borra tanto si se usa como si caducó."""
    with _lock:
        entry = _preview_tokens.pop(token, None)
    if entry is None:
        return None
    raw_bytes, expires_at = entry
    if datetime.now(timezone.utc) > expires_at:
        return None
    return raw_bytes


def purge_expired() -> None:
    """Purga de higiene (además de la perezosa en get/consume) — pensada para un job periódico."""
    now = datetime.now(timezone.utc)
    with _lock:
        for case_id, (_, expires_at) in list(_by_case_id.items()):
            if now > expires_at:
                del _by_case_id[case_id]
        for token, (_, expires_at) in list(_preview_tokens.items()):
            if now > expires_at:
                del _preview_tokens[token]
