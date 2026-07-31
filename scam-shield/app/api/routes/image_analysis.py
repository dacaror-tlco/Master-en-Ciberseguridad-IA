import hashlib
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.facial_search_case import FacialSearchCase
from app.models.image_case import ImageCase
from app.models.reverse_image_search_case import ReverseImageSearchCase
from app.schemas.image_analysis import (
    FacialSearchCaseResponse,
    ImageCaseListItem,
    ImageCaseResponse,
    ImageMatch,
    ReverseImageSearchCaseResponse,
)
from app.services import image_cache, image_service, integrity_payloads, integrity_service, pimeyes_service, serpapi_service
from app.services.image_risk_engine import evaluate_facial_search_risk, evaluate_image_risk, evaluate_reverse_search_risk

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/image-cases", tags=["image-cases"])

# Umbral de distancia de Hamming (sobre 64 bits) por debajo del cual dos
# imágenes se consideran "la misma foto" (permite recortes/recompresión
# leves). Cuanto más bajo, más estricta la coincidencia.
_SIMILARITY_THRESHOLD_BITS = 10

_REVERSE_SEARCH_LINKS = {
    "Google Images": "https://images.google.com/",
    "TinEye": "https://tineye.com/",
    "Yandex Images": "https://yandex.com/images/",
}

_IMAGE_FORMAT_TO_MEDIA_TYPE = {
    "JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif", "WEBP": "image/webp", "BMP": "image/bmp",
}


def _guess_media_type(raw_bytes: bytes) -> str:
    try:
        fmt = Image.open(BytesIO(raw_bytes)).format
    except Exception:
        return "application/octet-stream"
    return _IMAGE_FORMAT_TO_MEDIA_TYPE.get(fmt, "application/octet-stream")


def _get_image_case_or_404(case_id: int, db: Session) -> ImageCase:
    case = db.query(ImageCase).filter(ImageCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de imagen {case_id}")
    return case


def _get_cached_bytes_or_409(case_id: int) -> bytes:
    raw_bytes = image_cache.get(case_id)
    if raw_bytes is None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La imagen del caso {case_id} ya no está disponible en memoria (caducó a los 15 "
                "minutos, nunca se guarda en disco) — vuelve a analizarla con POST /analysis/image "
                "antes de pedir esta búsqueda"
            ),
        )
    return raw_bytes


@router.post("/image", response_model=ImageCaseResponse)
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ImageCase:
    raw_bytes = await file.read()

    try:
        phash, exif = image_service.analyze_image(raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Comparamos contra todos los casos de imagen ya guardados (dataset
    # pequeño en este proyecto, así que comparar uno a uno en Python es
    # más que suficiente — no hace falta ninguna estructura de índice).
    matches: list[ImageMatch] = []
    for existing in db.query(ImageCase).all():
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
        filename=file.filename,
        perceptual_hash=phash,
        risk_score=score,
        exif=exif.model_dump(mode="json"),
        matches=[m.model_dump(mode="json") for m in matches],
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=[],
        # Huella del ARCHIVO ORIGINAL (no solo del hash perceptual): la
        # prueba más fuerte posible de qué bytes exactos se analizaron, sin
        # necesidad de conservar la imagen. Solo informativa — NO entra en
        # la cadena verificable, ver integrity_payloads.py.
        raw_file_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "image", case.id, integrity_payloads.image_payload(case))

    # Guardamos los bytes SOLO en memoria (nunca en disco/BD), un rato corto,
    # por si luego se pide una búsqueda inversa (SerpApi) o facial (PimEyes)
    # sobre este mismo caso — así el usuario no tiene que resubir la foto.
    image_cache.put(case.id, raw_bytes)

    # Los enlaces de búsqueda inversa no se pueden pre-rellenar con la
    # imagen (no la alojamos en ningún sitio público) — llevan a la
    # herramienta para que el usuario suba la foto él mismo en un clic.
    response = ImageCaseResponse.model_validate(case)
    response.reverse_search_links = _REVERSE_SEARCH_LINKS
    return response


@router.get("/image/preview/{token}")
def preview_cached_image(token: str):
    """
    Sirve una imagen ya cacheada por un token opaco de un solo uso. Existe
    únicamente para que SerpApi pueda descargarla y completar la búsqueda
    inversa (Google no acepta subida directa de bytes, solo una URL
    pública) — ver `serpapi_service.py`. El token se borra tanto si se usa
    como si caduca (5 min), lo primero que ocurra.
    """
    raw_bytes = image_cache.consume_preview_token(token)
    if raw_bytes is None:
        raise HTTPException(status_code=404, detail="Enlace de previsualización inválido, ya usado o caducado")
    return Response(content=raw_bytes, media_type=_guess_media_type(raw_bytes))


@router.post("/image/{case_id}/reverse-search", response_model=ReverseImageSearchCaseResponse)
def reverse_search_image(case_id: int, db: Session = Depends(get_db)) -> ReverseImageSearchCase:
    """
    Búsqueda inversa de imagen vía SerpApi: ¿aparece esta foto en otras
    páginas de internet? Acción opcional y separada del análisis
    inicial — no se dispara automáticamente porque envía la imagen a un
    tercero (SerpApi/Google), a diferencia del resto del módulo de imagen
    que es 100% offline.
    """
    image_case = _get_image_case_or_404(case_id, db)
    raw_bytes = _get_cached_bytes_or_409(case_id)

    matches = []
    errors: list[str] = []
    reverse_search_links: dict[str, str] = {}
    try:
        token = image_cache.create_preview_token(raw_bytes)
        preview_url = f"{settings.public_base_url}/analysis/image/preview/{token}"
        matches = serpapi_service.reverse_image_search(preview_url)
    except Exception as exc:
        errors.append(f"SerpApi falló: {exc}")
        reverse_search_links = _REVERSE_SEARCH_LINKS

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
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(
        db, "image_reverse_search", case.id, integrity_payloads.reverse_image_search_payload(case)
    )

    response = ReverseImageSearchCaseResponse.model_validate(case)
    response.reverse_search_links = reverse_search_links
    return response


@router.post("/image/{case_id}/facial-search", response_model=FacialSearchCaseResponse)
def facial_search_image(
    case_id: int,
    confirmed_legal_basis: bool = Form(...),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
) -> FacialSearchCase:
    """
    Búsqueda de reconocimiento facial vía PimEyes: ¿esta cara aparece en
    otros perfiles/páginas? A diferencia del resto del módulo, esta acción
    procesa un dato biométrico (categoría especial bajo RGPD art. 9) — por
    eso NUNCA se dispara automáticamente, exige confirmar explícitamente
    que hay una base legal concreta para este caso (ej. documentar una
    usurpación de identidad para una denuncia — RGPD art. 9.2.f, ejercicio
    de reclamaciones legales), y esa confirmación queda sellada para
    siempre junto con los resultados en la cadena de integridad. Ver la
    sección "Reconocimiento facial (PimEyes) — uso acotado" del README.

    Esto no es asesoría legal — antes de un uso real en producción,
    consulta con un DPO/abogado si el caso concreto encaja en una base
    legal válida.
    """
    if not confirmed_legal_basis:
        raise HTTPException(
            status_code=422,
            detail=(
                "Para ejecutar una búsqueda facial hay que confirmar explícitamente "
                "(confirmed_legal_basis=true) que existe una base legal para este caso concreto "
                "— no se ejecuta reconocimiento facial sin esa confirmación"
            ),
        )

    image_case = _get_image_case_or_404(case_id, db)
    raw_bytes = _get_cached_bytes_or_409(case_id)

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
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(
        db, "image_facial_search", case.id, integrity_payloads.facial_search_payload(case)
    )

    return FacialSearchCaseResponse.model_validate(case)


@cases_router.get("", response_model=list[ImageCaseListItem])
def list_image_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(ImageCase)
        .order_by(desc(ImageCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=ImageCaseResponse)
def get_image_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(ImageCase).filter(ImageCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de imagen {case_id}")
    response = ImageCaseResponse.model_validate(case)
    response.reverse_search_links = _REVERSE_SEARCH_LINKS
    return response
