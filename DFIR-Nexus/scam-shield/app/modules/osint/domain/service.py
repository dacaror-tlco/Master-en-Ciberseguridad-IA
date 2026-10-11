"""
Orquestación del análisis de dominio: WHOIS + SSL + VirusTotal + DNS
completo (todas las IPs, MX, SPF/DMARC, CAA) + reputación de cada IP
(AbuseIPDB) + subdominios relacionados (crt.sh) + historial (Wayback
Machine) + scoring + persistencia + cadena de custodia + registro en
monitorización continua.

Vive separado de la ruta para poder reutilizarse tal cual desde el
scheduler de monitorización (ver monitoring/runner.py), que necesita
re-ejecutar exactamente el mismo pipeline que el análisis manual.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.osint.domain import crtsh_service, repository, wayback_service
from app.modules.osint.domain.models import Case
from app.modules.osint.shared.schemas import IpReputationEntry
from app.modules.osint.shared import abuseipdb_service, dns_service, ssl_service, virustotal_service, whois_service
from app.modules.osint.shared.domain_utils import normalize_domain
from app.modules.osint.shared.risk_engine import evaluate_risk
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.findings import service as findings_service
from app.modules.osint.monitoring import service as monitoring_service

# Tope de IPs a las que se les consulta AbuseIPDB por dominio: un dominio
# detrás de un CDN grande puede resolver a decenas de IPs (anycast), y
# consultarlas todas agotaría en segundos el límite gratuito de AbuseIPDB
# sin aportar señal extra más allá de las primeras.
_MAX_IPS_CHECKED = 5


def run_domain_analysis(db: Session, domain: str, case_id: int | None = None) -> Case:
    domain = normalize_domain(domain)

    errors: list[str] = []

    whois_info = None
    try:
        whois_info = whois_service.get_whois_info(domain)
    except Exception as exc:  # las fuentes externas fallan a menudo (rate limit, dominio inexistente...)
        errors.append(f"WHOIS falló: {exc}")

    ssl_info = None
    try:
        ssl_info = ssl_service.get_ssl_info(domain)
    except Exception as exc:
        errors.append(f"SSL falló: {exc}")

    vt_info = None
    try:
        vt_info = virustotal_service.get_virustotal_info(domain)
    except Exception as exc:
        errors.append(f"VirusTotal falló: {exc}")

    dns_info = None
    try:
        dns_info = dns_service.get_dns_records(domain)
    except Exception as exc:
        errors.append(f"No se pudo resolver el dominio a una IP — se omiten DNS/reputación de IP: {exc}")

    resolved_ip = dns_info.all_ips[0] if dns_info and dns_info.all_ips else None
    abuseipdb_info = None
    ip_reputations: list[IpReputationEntry] = []
    if dns_info and dns_info.all_ips:
        for ip in dns_info.all_ips[:_MAX_IPS_CHECKED]:
            try:
                info = abuseipdb_service.get_ip_reputation(ip)
            except Exception as exc:
                errors.append(f"AbuseIPDB falló para {ip}: {exc}")
                continue
            ip_reputations.append(IpReputationEntry(ip=ip, abuseipdb=info))
            if ip == resolved_ip:
                abuseipdb_info = info

    crtsh_info = None
    try:
        crtsh_info = crtsh_service.get_crtsh_info(domain)
    except Exception as exc:
        errors.append(f"crt.sh falló: {exc}")

    wayback_info = None
    try:
        wayback_info = wayback_service.get_wayback_info(domain)
    except Exception as exc:
        errors.append(f"Wayback Machine falló: {exc}")

    flags, score = evaluate_risk(
        whois_info, ssl_info, vt_info, abuseipdb_info,
        dns_info, ip_reputations, crtsh_info, wayback_info, resolved_ip,
    )

    case = repository.create_case(
        db,
        domain=domain,
        case_id=case_id,
        analyzed_at=datetime.now(timezone.utc),
        whois=whois_info.model_dump(mode="json") if whois_info else None,
        ssl=ssl_info.model_dump(mode="json") if ssl_info else None,
        virustotal=vt_info.model_dump(mode="json") if vt_info else None,
        resolved_ip=resolved_ip,
        abuseipdb=abuseipdb_info.model_dump(mode="json") if abuseipdb_info else None,
        dns=dns_info.model_dump(mode="json") if dns_info else None,
        ip_reputations=[entry.model_dump(mode="json") for entry in ip_reputations],
        crtsh=crtsh_info.model_dump(mode="json") if crtsh_info else None,
        wayback=wayback_info.model_dump(mode="json") if wayback_info else None,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        risk_score=score,
        errors=errors,
    )

    integrity_service.record_evidence(db, "domain", case.id, integrity_payloads.domain_payload(case))
    findings_service.record_finding(db, "domain", case)
    monitoring_service.touch_subject(db, "domain", domain, case.id, score, flags)

    return case


def get_case(db: Session, case_id: int) -> Case | None:
    return repository.get_case(db, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[Case]:
    return repository.list_cases(db, skip, limit)
