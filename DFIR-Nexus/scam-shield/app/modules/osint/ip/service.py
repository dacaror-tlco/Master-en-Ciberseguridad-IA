"""Orquestación del análisis de IP: validación de formato + reputación (AbuseIPDB) + scoring + persistencia + cadena de custodia + registro en monitorización continua. Reutilizado por la ruta manual y por el scheduler de monitorización."""
import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.osint.ip import repository
from app.modules.osint.ip.models import IpCase
from app.modules.osint.shared import abuseipdb_service
from app.modules.osint.shared.ip_risk_engine import evaluate_ip_risk
from app.modules.osint.findings import service as findings_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.monitoring import service as monitoring_service


def run_ip_analysis(db: Session, raw_ip: str, case_id: int | None = None) -> IpCase:
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
        case_id=case_id,
        abuseipdb=abuseipdb_info.model_dump(mode="json") if abuseipdb_info else None,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    case = repository.create_case(db, case)

    integrity_service.record_evidence(db, "ip", case.id, integrity_payloads.ip_payload(case))
    findings_service.record_finding(db, "ip", case)
    monitoring_service.touch_subject(db, "ip", ip, case.id, score, flags)

    return case


def get_case(db: Session, case_id: int) -> IpCase | None:
    return repository.get_case(db, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[IpCase]:
    return repository.list_cases(db, skip, limit)
