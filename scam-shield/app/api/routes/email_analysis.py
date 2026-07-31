import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.email_case import EmailCase
from app.schemas.email_analysis import (
    EmailAnalysisRequest,
    EmailCaseListItem,
    EmailCaseResponse,
)
from app.services import abuseipdb_service, ai_service, email_link_analysis, integrity_payloads, integrity_service, whois_service
from app.services.email_risk_engine import evaluate_email_risk
from app.services.email_service import (
    extract_attachments,
    extract_links,
    looks_like_raw_source,
    parse_email_headers_from_message,
    parse_email_message,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/email-cases", tags=["email-cases"])


def _analyze_and_save(raw_email: str, db: Session) -> EmailCase:
    """Lógica compartida entre el endpoint JSON y el de subida de archivo."""
    errors: list[str] = []

    try:
        msg = parse_email_message(raw_email)
        headers = parse_email_headers_from_message(msg)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo parsear el email: {exc}")

    is_raw_source = looks_like_raw_source(msg)

    sender_whois = None
    if headers.from_address and "@" in headers.from_address:
        sender_domain = headers.from_address.rsplit("@", 1)[-1]
        try:
            sender_whois = whois_service.get_whois_info(sender_domain)
        except Exception as exc:
            errors.append(f"WHOIS del dominio remitente falló: {exc}")

    links = email_link_analysis.analyze_links(extract_links(msg))
    attachments = extract_attachments(msg)

    originating_ip_abuseipdb = None
    if headers.originating_ip:
        try:
            originating_ip_abuseipdb = abuseipdb_service.get_ip_reputation(headers.originating_ip)
        except Exception as exc:
            errors.append(f"AbuseIPDB para la IP de origen ({headers.originating_ip}) falló: {exc}")

    flags, score = evaluate_email_risk(
        headers, sender_whois, links, attachments, is_raw_source, originating_ip_abuseipdb
    )

    case = EmailCase(
        from_address=headers.from_address,
        subject=headers.subject,
        risk_score=score,
        headers=headers.model_dump(mode="json"),
        sender_domain_whois=sender_whois.model_dump(mode="json") if sender_whois else None,
        originating_ip_abuseipdb=originating_ip_abuseipdb.model_dump(mode="json") if originating_ip_abuseipdb else None,
        links=[link.model_dump(mode="json") for link in links],
        attachments=[att.model_dump(mode="json") for att in attachments],
        is_raw_source=is_raw_source,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        # Huella del email ORIGINAL en crudo: la prueba más fuerte de "esto es
        # exactamente lo que se analizó", sin necesidad de conservar el
        # contenido (seguimos sin guardarlo, por privacidad). Es solo
        # informativa — NO entra en la cadena verificable, ver integrity_payloads.py.
        raw_email_sha256=hashlib.sha256(raw_email.encode("utf-8")).hexdigest(),
        analyzed_at=datetime.now(timezone.utc),
    )

    # La narrativa en lenguaje sencillo es un extra opcional (solo si hay
    # ANTHROPIC_API_KEY): nunca debe impedir guardar el análisis si falla
    # o no está configurada.
    try:
        case.ai_explanation = ai_service.generate_email_narrative(case)
    except Exception as exc:
        errors.append(f"Explicación con IA no disponible: {exc}")

    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "email", case.id, integrity_payloads.email_payload(case))

    return case


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
    return _analyze_and_save(payload.raw_email, db)


@router.post("/email/file", response_model=EmailCaseResponse)
async def analyze_email_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> EmailCase:
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

    return _analyze_and_save(raw_email, db)


@cases_router.get("", response_model=list[EmailCaseListItem])
def list_email_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(EmailCase)
        .order_by(desc(EmailCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=EmailCaseResponse)
def get_email_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(EmailCase).filter(EmailCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de email {case_id}")
    return case
