from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.osint.image import image_cache, service
from app.modules.osint.image.models import FacialSearchCase, ImageCase, ReverseImageSearchCase
from app.modules.osint.image.schemas import (
    FacialSearchCaseResponse,
    ImageCaseListItem,
    ImageCaseResponse,
    ReverseImageSearchCaseResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/image-cases", tags=["image-cases"])

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
    case = service.get_image_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de imagen {case_id}")
    return case


@router.post("/image", response_model=ImageCaseResponse)
async def analyze_image(
    file: UploadFile = File(...),
    case_id: int | None = Form(None, description="Expediente de Nexus (cases.id) al que pertenece este análisis, si procede."),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ImageCase:
    raw_bytes = await file.read()
    try:
        case = service.analyze_image(db, file.filename, raw_bytes, case_id=case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Los enlaces de búsqueda inversa no se pueden pre-rellenar con la
    # imagen (no la alojamos en ningún sitio público) — llevan a la
    # herramienta para que el usuario suba la foto él mismo en un clic.
    response = ImageCaseResponse.model_validate(case)
    response.reverse_search_links = service.REVERSE_SEARCH_LINKS
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
def reverse_search_image(
    case_id: int, db: Session = Depends(get_db), _user: dict = Depends(get_current_user)
) -> ReverseImageSearchCase:
    image_case = _get_image_case_or_404(case_id, db)
    try:
        case, reverse_search_links = service.reverse_search_image(db, image_case)
    except LookupError:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La imagen del caso {case_id} ya no está disponible en memoria (caducó a los 15 "
                "minutos, nunca se guarda en disco) — vuelve a analizarla con POST /analysis/image "
                "antes de pedir esta búsqueda"
            ),
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
    _user: dict = Depends(get_current_user),
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
    try:
        case = service.facial_search_image(db, image_case, confirmed_legal_basis, notes)
    except LookupError:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La imagen del caso {case_id} ya no está disponible en memoria (caducó a los 15 "
                "minutos, nunca se guarda en disco) — vuelve a analizarla con POST /analysis/image "
                "antes de pedir esta búsqueda"
            ),
        )

    return FacialSearchCaseResponse.model_validate(case)


@cases_router.get("", response_model=list[ImageCaseListItem])
def list_image_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_image_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=ImageCaseResponse)
def get_image_case(case_id: int, db: Session = Depends(get_db)):
    case = _get_image_case_or_404(case_id, db)
    response = ImageCaseResponse.model_validate(case)
    response.reverse_search_links = service.REVERSE_SEARCH_LINKS
    return response
