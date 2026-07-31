from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import Case
from app.models.cnmv_check_case import CnmvCheckCase
from app.models.email_case import EmailCase
from app.models.facial_search_case import FacialSearchCase
from app.models.image_case import ImageCase
from app.models.ip_case import IpCase
from app.models.phone_case import PhoneCase
from app.models.reverse_image_search_case import ReverseImageSearchCase
from app.models.typosquatting_case import TyposquattingCase
from app.models.wallet_case import WalletCase
from app.schemas.report import ReportRequest
from app.services import integrity_service, reporting_service
from app.services.report_service import build_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
def generate_report(payload: ReportRequest, db: Session = Depends(get_db)) -> Response:
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
    reporting_channels = reporting_service.recommend_channels(included_types)

    pdf_bytes = build_report_pdf(
        domain_cases, email_cases, wallet_cases, payload.victim_notes, payload.ai_narrative,
        typosquatting_cases, phone_cases, cnmv_cases, image_cases,
        ledger_entries, chain_intact, reporting_channels,
        reverse_image_search_cases, facial_search_cases, ip_cases,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="informe_scamshield.pdf"'},
    )
