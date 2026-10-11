"""Orquestación del análisis de email: parseo + WHOIS del remitente + enlaces + adjuntos + IP de origen + scoring + persistencia + cadena de custodia."""
import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.osint.email import repository
from app.modules.osint.email.email_service import (
    extract_attachments,
    extract_links,
    looks_like_raw_source,
    parse_email_headers_from_message,
    parse_email_message,
)
from app.modules.osint.email.link_analysis import analyze_links
from app.modules.osint.email.models import EmailCase
from app.modules.osint.email.risk_engine import evaluate_email_risk
from app.modules.osint.findings import service as findings_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.shared import abuseipdb_service, ai_service, whois_service


def analyze_and_save(raw_email: str, db: Session, case_id: int | None = None) -> EmailCase:
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

    links = analyze_links(extract_links(msg))
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
        case_id=case_id,
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
        # informativa — NO entra en la cadena verificable, ver integrity/payloads.py.
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

    case = repository.create_case(db, case)

    integrity_service.record_evidence(db, "email", case.id, integrity_payloads.email_payload(case))
    findings_service.record_finding(db, "email", case)

    return case


def get_case(db: Session, case_id: int) -> EmailCase | None:
    return repository.get_case(db, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[EmailCase]:
    return repository.list_cases(db, skip, limit)
