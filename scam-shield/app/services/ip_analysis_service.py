"""
Orquestación del análisis de IP: validación de formato + reputación
(AbuseIPDB) + scoring + persistencia + cadena de custodia + registro en
monitorización continua. Reutilizado por la ruta manual y por el
scheduler de monitorización.
"""
import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ip_case import IpCase
from app.services import abuseipdb_service, integrity_payloads, integrity_service, monitoring_service
from app.services.ip_risk_engine import evaluate_ip_risk


def run_ip_analysis(db: Session, raw_ip: str) -> IpCase:
    ip = raw_ip.strip()
    ipaddress.ip_address(ip)  # ValueError (formato no reconocido) se deja subir tal cual, igual que en teléfono/dominio

    errors: list[str] = []
    abuseipdb_info = None
    try:
        abuseipdb_info = abuseipdb_service.get_ip_reputation(ip)
    except Exception as exc:
        errors.append(f"AbuseIPDB falló: {exc}")

    flags, score = evaluate_ip_risk(abuseipdb_info)

    case = IpCase(
        ip=ip,
        risk_score=score,
        abuseipdb=abuseipdb_info.model_dump(mode="json") if abuseipdb_info else None,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "ip", case.id, integrity_payloads.ip_payload(case))
    monitoring_service.touch_subject(db, "ip", ip, case.id, score, flags)

    return case
