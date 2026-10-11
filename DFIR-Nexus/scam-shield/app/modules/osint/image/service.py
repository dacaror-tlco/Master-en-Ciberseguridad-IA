"""Orquestación del análisis de imagen: EXIF + hash perceptual + coincidencias con otros casos + scoring + persistencia + cadena de custodia, más las dos acciones opcionales separadas (SerpApi/PimEyes) sobre un caso ya analizado."""
import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.osint.image import image_cache, image_service, pimeyes_service, repository, serpapi_service
from app.modules.osint.image.models import FacialSearchCase, ImageCase, ReverseImageSearchCase
from app.modules.osint.image.risk_engine import evaluate_facial_search_risk, evaluate_image_risk, evaluate_reverse_search_risk
from app.modules.osint.image.schemas import ImageMatch
from app.modules.osint.findings import service as findings_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.integrity import service as integrity_service

# Umbral de distancia de Hamming (sobre 64 bits) por debajo del cual dos
# imágenes se consideran "la misma foto" (permite recortes/recompresión
# leves). Cuanto más bajo, más estricta la coincidencia.
_SIMILARITY_THRESHOLD_BITS = 10

REVERSE_SEARCH_LINKS = {
    "Google Images": "https://images.google.com/",
    "TinEye": "https://tineye.com/",
    "Yandex Images": "https://yandex.com/images/",
}


def analyze_image(db: Session, filename: str | None, raw_bytes: bytes, case_id: int | None = None) -> ImageCase:
    try:
        phash, exif = image_service.analyze_image(raw_bytes)
    except ValueError:
        raise

    # Comparamos contra todos los casos de imagen ya guardados (dataset
    # pequeño en este proyecto, así que comparar uno a uno en Python es
    # más que suficiente — no hace falta ninguna estructura de índice).
    matches: list[ImageMatch] = []
    for existing in repository.all_image_cases(db):
        distance = image_service.hamming_distance(phash, existing.perceptual_hash)
        if distance <= _SIMILARITY_THRESHOLD_BITS:
            matches.append(ImageMatch(
                case_id=existing.id,
                filename=existing.filename,
                similarity_percent=image_service.similarity_percent(phash, existing.perceptual_hash),
                analyzed_at=existing.analyzed_at,
            ))

    flags, score = evaluate_image_risk(exif, matches)

    case = ImageCase(
        filename=filename,
        perceptual_hash=phash,
        risk_score=score,
        case_id=case_id,
        exif=exif.model_dump(mode="json"),
        matches=[m.model_dump(mode="json") for m in matches],
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=[],
        # Huella del ARCHIVO ORIGINAL (no solo del hash perceptual): la
        # prueba más fuerte posible de qué bytes exactos se analizaron, sin
        # necesidad de conservar la imagen. Solo informativa — NO entra en
        # la cadena verificable, ver integrity/payloads.py.
        raw_file_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        analyzed_at=datetime.now(timezone.utc),
    )
    case = repository.create_image_case(db, case)

    integrity_service.record_evidence(db, "image", case.id, integrity_payloads.image_payload(case))
    findings_service.record_finding(db, "image", case)

    # Guardamos los bytes SOLO en memoria (nunca en disco/BD), un rato corto,
    # por si luego se pide una búsqueda inversa (SerpApi) o facial (PimEyes)
    # sobre este mismo caso — así el usuario no tiene que resubir la foto.
    image_cache.put(case.id, raw_bytes)

    return case


def get_image_case(db: Session, case_id: int) -> ImageCase | None:
    return repository.get_image_case(db, case_id)


def list_image_cases(db: Session, skip: int = 0, limit: int = 50) -> list[ImageCase]:
    return repository.list_image_cases(db, skip, limit)


def reverse_search_image(db: Session, image_case: ImageCase) -> tuple[ReverseImageSearchCase, dict[str, str]]:
    """
    Búsqueda inversa de imagen vía SerpApi: ¿aparece esta foto en otras
    páginas de internet? Acción opcional y separada del análisis
    inicial — no se dispara automáticamente porque envía la imagen a un
    tercero (SerpApi/Google), a diferencia del resto del módulo de imagen
    que es 100% offline.
    """
    raw_bytes = image_cache.get(image_case.id)
    if raw_bytes is None:
        raise LookupError(image_case.id)

    matches = []
    errors: list[str] = []
    reverse_search_links: dict[str, str] = {}
    try:
        token = image_cache.create_preview_token(raw_bytes)
        preview_url = f"{settings.public_base_url}/analysis/image/preview/{token}"
        matches = serpapi_service.reverse_image_search(preview_url)
    except Exception as exc:
        errors.append(f"SerpApi falló: {exc}")
        reverse_search_links = REVERSE_SEARCH_LINKS

    flags, score = evaluate_reverse_search_risk(matches)

    case = ReverseImageSearchCase(
        image_case_id=image_case.id,
        source_sha256=image_case.raw_file_sha256,
        matches=[m.model_dump(mode="json") for m in matches],
        risk_flags=[f.model_dump(mode="json") for f in flags],
        risk_score=score,
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    case = repository.create_reverse_search_case(db, case)

    integrity_service.record_evidence(
        db, "image_reverse_search", case.id, integrity_payloads.reverse_image_search_payload(case)
    )
    findings_service.record_finding(db, "image_reverse_search", case)

    return case, reverse_search_links


def facial_search_image(db: Session, image_case: ImageCase, confirmed_legal_basis: bool, notes: str | None) -> FacialSearchCase:
    """
    Búsqueda de reconocimiento facial vía PimEyes: ¿esta cara aparece en
    otros perfiles/páginas? Procesa un dato biométrico (RGPD art. 9) —
    exige `confirmed_legal_basis` (validado por quien llama, ver routes.py)
    y la confirmación queda sellada junto con los resultados en la cadena
    de integridad.
    """
    raw_bytes = image_cache.get(image_case.id)
    if raw_bytes is None:
        raise LookupError(image_case.id)

    matches = []
    errors: list[str] = []
    try:
        matches = pimeyes_service.search_face(raw_bytes)
    except Exception as exc:
        errors.append(f"PimEyes falló: {exc}")

    flags, score = evaluate_facial_search_risk(matches)

    case = FacialSearchCase(
        image_case_id=image_case.id,
        source_sha256=image_case.raw_file_sha256,
        confirmed_legal_basis=confirmed_legal_basis,
        notes=notes,
        matches=[m.model_dump(mode="json") for m in matches],
        risk_flags=[f.model_dump(mode="json") for f in flags],
        risk_score=score,
        errors=errors,
        requested_at=datetime.now(timezone.utc),
    )
    case = repository.create_facial_search_case(db, case)

    integrity_service.record_evidence(
        db, "image_facial_search", case.id, integrity_payloads.facial_search_payload(case)
    )
    findings_service.record_finding(db, "image_facial_search", case)

    return case
