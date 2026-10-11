from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.email import service
from app.modules.osint.email.models import EmailCase
from app.modules.osint.email.schemas import EmailAnalysisRequest, EmailCaseListItem, EmailCaseResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/email-cases", tags=["email-cases"])


@router.post("/email", response_model=EmailCaseResponse)
def analyze_email(payload: EmailAnalysisRequest, db: Session = Depends(get_db)) -> EmailCase:
    """
    Pensado para uso programático (el frontend —incluida la opción de pegar
    texto directamente—, o llamadas desde código), donde el JSON se
    construye correctamente y los saltos de línea ya vienen escapados. Para
    probar a mano desde Swagger, usa mejor /analysis/email/file — te ahorras
    el problema de JSON inválido al pegar texto con saltos de línea reales.

    Acepta tanto el código fuente real del email como, si no se dispone de
    él, el texto visible tal cual: ver `is_raw_source` en la respuesta.
    """
    return service.analyze_and_save(payload.raw_email, db, case_id=payload.case_id)


@router.post("/email/file", response_model=EmailCaseResponse)
async def analyze_email_file(
    file: UploadFile = File(...),
    case_id: int | None = Form(None, description="Expediente de Nexus (cases.id) al que pertenece este análisis, si procede."),
    db: Session = Depends(get_db),
) -> EmailCase:
    """
    Sube directamente el email como archivo (.eml o .txt con el código
    fuente del mensaje). Es la forma recomendada de probarlo a mano, y
    también cómo funcionará en el frontend real (arrastrar el archivo).
    """
    raw_bytes = await file.read()
    try:
        raw_email = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_email = raw_bytes.decode("latin-1")  # algunos clientes de correo antiguos no usan UTF-8

    return service.analyze_and_save(raw_email, db, case_id=case_id)


@cases_router.get("", response_model=list[EmailCaseListItem])
def list_email_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=EmailCaseResponse)
def get_email_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de email {case_id}")
    return case
