"""
Orquestación del análisis de teléfono: parseo + reportes comunitarios
(OpenSpam) + puntuación de fraude (IPQualityScore) + carrier en tiempo
real (Twilio Lookup) + scoring + persistencia + cadena de custodia +
registro en monitorización continua. Reutilizado por la ruta manual y
por el scheduler de monitorización — ojo con esto último si se configura
Twilio: cada re-chequeo periódico de un teléfono monitorizado también lo
consulta a él (es un servicio de pago), ver README.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.phone_case import PhoneCase
from app.services import (
    integrity_payloads,
    integrity_service,
    ipqualityscore_service,
    monitoring_service,
    openspam_service,
    phone_service,
    twilio_lookup_service,
)
from app.services.phone_risk_engine import evaluate_phone_risk


def run_phone_analysis(db: Session, raw_phone: str, default_region: str) -> PhoneCase:
    # ValueError (formato no reconocido) se deja subir tal cual: quien llame decide cómo traducirla.
    phone_info = phone_service.analyze_phone(raw_phone, default_region)

    errors: list[str] = []
    community_info = None
    try:
        community_info = openspam_service.get_community_reports(phone_info.e164)
    except Exception as exc:
        errors.append(f"OpenSpam falló: {exc}")

    fraud_info = None
    try:
        fraud_info = ipqualityscore_service.get_fraud_score(phone_info.e164)
    except Exception as exc:
        errors.append(f"IPQualityScore falló: {exc}")

    carrier_intel = None
    try:
        carrier_intel = twilio_lookup_service.get_carrier_intelligence(phone_info.e164)
    except Exception as exc:
        errors.append(f"Twilio Lookup falló: {exc}")

    flags, score = evaluate_phone_risk(phone_info, community_info, fraud_info, carrier_intel)

    case = PhoneCase(
        raw_phone=raw_phone.strip(),
        line_type=phone_info.line_type,
        risk_score=score,
        phone=phone_info.model_dump(mode="json"),
        community_reports=community_info.model_dump(mode="json") if community_info else None,
        fraud_score=fraud_info.model_dump(mode="json") if fraud_info else None,
        carrier_intelligence=carrier_intel.model_dump(mode="json") if carrier_intel else None,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "phone", case.id, integrity_payloads.phone_payload(case))
    # Identificador = e164 (formato canónico), no el texto tal cual lo escribió el usuario:
    # así dos formas distintas de escribir el mismo número (local vs internacional) se
    # tratan como el mismo sujeto monitorizado en vez de crear dos entradas separadas.
    monitoring_service.touch_subject(db, "phone", phone_info.e164, case.id, score, flags)

    return case
