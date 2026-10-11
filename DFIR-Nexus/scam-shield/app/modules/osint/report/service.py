"""Orquestación de generación de informe PDF y valoración consolidada con IA — lee casos de TODOS los sub-módulos de OSINT a propósito (es la función que los combina), ver correlation_service.py/pdf_builder.py."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.osint.cnmv.models import CnmvCheckCase
from app.modules.osint.domain.models import Case
from app.modules.osint.email.models import EmailCase
from app.modules.osint.image.models import FacialSearchCase, ImageCase, ReverseImageSearchCase
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.ip.models import IpCase
from app.modules.osint.phone.models import PhoneCase
from app.modules.osint.report.correlation_service import find_correlations
from app.modules.osint.report.pdf_builder import build_report_pdf
from app.modules.osint.report.reporting_service import recommend_channels
from app.modules.osint.report.schemas import ConsolidatedRequest, ConsolidatedResponse, ReportRequest
from app.modules.osint.shared import ai_service
from app.modules.osint.typosquatting.models import TyposquattingCase
from app.modules.osint.wallet.models import WalletCase


def generate_report_pdf(db: Session, payload: ReportRequest) -> bytes:
    if not (
        payload.domain_case_ids or payload.email_case_ids or payload.wallet_case_ids
        or payload.typosquatting_case_ids or payload.phone_case_ids or payload.cnmv_check_case_ids
        or payload.image_case_ids or payload.ip_case_ids
    ):
        raise HTTPException(status_code=400, detail="Indica al menos un caso (dominio, email, wallet, typosquatting, teléfono, CNMV, imagen o IP) para generar el informe")

    domain_cases = db.query(Case).filter(Case.id.in_(payload.domain_case_ids)).all() if payload.domain_case_ids else []
    email_cases = db.query(EmailCase).filter(EmailCase.id.in_(payload.email_case_ids)).all() if payload.email_case_ids else []
    wallet_cases = db.query(WalletCase).filter(WalletCase.id.in_(payload.wallet_case_ids)).all() if payload.wallet_case_ids else []
    typosquatting_cases = (
        db.query(TyposquattingCase).filter(TyposquattingCase.id.in_(payload.typosquatting_case_ids)).all()
        if payload.typosquatting_case_ids else []
    )
    phone_cases = db.query(PhoneCase).filter(PhoneCase.id.in_(payload.phone_case_ids)).all() if payload.phone_case_ids else []
    cnmv_cases = (
        db.query(CnmvCheckCase).filter(CnmvCheckCase.id.in_(payload.cnmv_check_case_ids)).all()
        if payload.cnmv_check_case_ids else []
    )
    image_cases = db.query(ImageCase).filter(ImageCase.id.in_(payload.image_case_ids)).all() if payload.image_case_ids else []
    ip_cases = db.query(IpCase).filter(IpCase.id.in_(payload.ip_case_ids)).all() if payload.ip_case_ids else []

    # Búsquedas opcionales (SerpApi/PimEyes) ya ejecutadas sobre esos casos de
    # imagen, si las hay — se incluyen automáticamente en el informe sin que
    # haga falta seleccionarlas aparte, igual que EXIF/hash van pegados al caso.
    image_case_ids = [c.id for c in image_cases]
    reverse_image_search_cases = (
        db.query(ReverseImageSearchCase).filter(ReverseImageSearchCase.image_case_id.in_(image_case_ids)).all()
        if image_case_ids else []
    )
    facial_search_cases = (
        db.query(FacialSearchCase).filter(FacialSearchCase.image_case_id.in_(image_case_ids)).all()
        if image_case_ids else []
    )

    found_ids = (
        {c.id for c in domain_cases} | {c.id for c in email_cases}
        | {c.id for c in wallet_cases} | {c.id for c in typosquatting_cases}
        | {c.id for c in phone_cases} | {c.id for c in cnmv_cases}
        | {c.id for c in image_cases} | {c.id for c in ip_cases}
    )
    requested_ids = (
        set(payload.domain_case_ids) | set(payload.email_case_ids)
        | set(payload.wallet_case_ids) | set(payload.typosquatting_case_ids)
        | set(payload.phone_case_ids) | set(payload.cnmv_check_case_ids)
        | set(payload.image_case_ids) | set(payload.ip_case_ids)
    )
    missing = requested_ids - found_ids
    if missing:
        raise HTTPException(status_code=404, detail=f"No se encontraron los siguientes casos: {sorted(missing)}")

    # Certificado de integridad: el eslabón de cada caso incluido, más el
    # veredicto de si la cadena COMPLETA (no solo estos casos) sigue intacta.
    included = (
        [("domain", c.id) for c in domain_cases] + [("email", c.id) for c in email_cases]
        + [("wallet", c.id) for c in wallet_cases] + [("typosquatting", c.id) for c in typosquatting_cases]
        + [("phone", c.id) for c in phone_cases] + [("cnmv", c.id) for c in cnmv_cases]
        + [("image", c.id) for c in image_cases]
        + [("image_reverse_search", c.id) for c in reverse_image_search_cases]
        + [("image_facial_search", c.id) for c in facial_search_cases]
        + [("ip", c.id) for c in ip_cases]
    )
    ledger_entries = [
        entry for case_type, case_id in included
        if (entry := integrity_service.get_entry_for_case(db, case_type, case_id)) is not None
    ]
    chain_intact, _ = integrity_service.verify_chain(db)

    included_types = {ct for ct, _ in included}
    reporting_channels = recommend_channels(included_types)

    return build_report_pdf(
        domain_cases, email_cases, wallet_cases, payload.victim_notes, payload.ai_narrative,
        typosquatting_cases, phone_cases, cnmv_cases, image_cases,
        ledger_entries, chain_intact, reporting_channels,
        reverse_image_search_cases, facial_search_cases, ip_cases,
    )


def consolidated_assessment(db: Session, payload: ConsolidatedRequest) -> ConsolidatedResponse:
    if not (payload.domain_case_ids or payload.email_case_ids or payload.wallet_case_ids or payload.typosquatting_case_ids):
        raise HTTPException(status_code=400, detail="Indica al menos un caso (dominio, email, wallet o typosquatting) para el análisis consolidado")

    domain_cases = db.query(Case).filter(Case.id.in_(payload.domain_case_ids)).all() if payload.domain_case_ids else []
    email_cases = db.query(EmailCase).filter(EmailCase.id.in_(payload.email_case_ids)).all() if payload.email_case_ids else []
    wallet_cases = db.query(WalletCase).filter(WalletCase.id.in_(payload.wallet_case_ids)).all() if payload.wallet_case_ids else []
    typosquatting_cases = (
        db.query(TyposquattingCase).filter(TyposquattingCase.id.in_(payload.typosquatting_case_ids)).all()
        if payload.typosquatting_case_ids else []
    )

    all_scores = [c.risk_score for c in (*domain_cases, *email_cases, *wallet_cases, *typosquatting_cases)]
    base_score = max(all_scores) if all_scores else 0

    correlation_flags = find_correlations(domain_cases, email_cases, wallet_cases, typosquatting_cases)
    # La correlación entre módulos sube el score base: es una señal más fuerte
    # que cualquier señal aislada, porque confirma que es la misma infraestructura.
    consolidated_score = min(base_score + (15 if correlation_flags else 0), 100)

    narrative = None
    narrative_error = None
    if payload.include_ai_narrative:
        try:
            narrative = ai_service.generate_narrative(
                domain_cases, email_cases, wallet_cases, correlation_flags, payload.victim_notes
            )
        except Exception as exc:
            narrative_error = str(exc)

    return ConsolidatedResponse(
        consolidated_score=consolidated_score,
        correlation_flags=correlation_flags,
        ai_narrative=narrative,
        ai_narrative_error=narrative_error,
    )
