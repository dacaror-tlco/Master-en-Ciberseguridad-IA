"""
Orquestación del análisis de typosquatting: generación de variantes +
comprobación DNS + reputación de IP (barata, todas las variantes activas)
+ (opcional) análisis en profundidad (caro, limitado) + scoring +
persistencia + cadena de custodia + registro en monitorización continua.
Reutilizado por la ruta manual y por el scheduler de monitorización.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.typosquatting_case import TyposquattingCase
from app.schemas.domain_analysis import AbuseIpInfo
from app.schemas.typosquatting import TyposquattingCandidate
from app.services import abuseipdb_service, dns_service, integrity_payloads, integrity_service, monitoring_service, ssl_service, typosquatting_service, virustotal_service, whois_service
from app.services.domain_utils import normalize_domain
from app.services.ip_risk_engine import evaluate_ip_risk
from app.services.risk_engine import evaluate_risk
from app.services.typosquatting_risk_engine import evaluate_typosquatting_risk


def run_typosquatting_analysis(
    db: Session,
    domain: str,
    max_variants: int = 200,
    include_full_analysis: bool = False,
    max_full_analysis: int = 4,
    max_ip_checks: int = 50,
) -> TyposquattingCase:
    domain = normalize_domain(domain)

    variant_pairs = typosquatting_service.generate_variants(domain, limit=max_variants)
    errors: list[str] = []

    if not variant_pairs:
        raise ValueError(f"No se pudo procesar '{domain}' (formato de dominio no reconocido)")

    dns_results = dns_service.check_dns_bulk([v for v, _ in variant_pairs])

    candidates: list[TyposquattingCandidate] = []
    for variant, technique in variant_pairs:
        ip = dns_results.get(variant)
        if ip:
            candidates.append(TyposquattingCandidate(variant=variant, technique=technique, resolves=True, ip_address=ip))

    # Reputación de IP (AbuseIPDB): a diferencia de WHOIS/SSL/VirusTotal
    # (por dominio, caros/limitados), esto consulta por IP y es barato —
    # se aplica a TODAS las variantes activas (hasta max_ip_checks IPs
    # únicas, con caché por IP para no repetir consulta si varias
    # variantes comparten hosting, algo típico en campañas grandes).
    ip_reputation_cache: dict[str, AbuseIpInfo | None] = {}
    if not settings.abuseipdb_api_key:
        if candidates:
            errors.append("AbuseIPDB no configurada — se omite la reputación de IP de las variantes activas")
    else:
        for candidate in candidates:
            ip = candidate.ip_address
            if ip not in ip_reputation_cache:
                if len(ip_reputation_cache) >= max_ip_checks:
                    continue  # tope de IPs únicas alcanzado, el resto se queda sin esta señal (no es un error)
                try:
                    ip_reputation_cache[ip] = abuseipdb_service.get_ip_reputation(ip)
                except Exception as exc:
                    ip_reputation_cache[ip] = None
                    errors.append(f"AbuseIPDB de {ip} falló: {exc}")
            abuseipdb_info = ip_reputation_cache.get(ip)
            if abuseipdb_info:
                candidate.abuseipdb = abuseipdb_info
                ip_flags, ip_score = evaluate_ip_risk(abuseipdb_info)
                candidate.risk_score = ip_score
                candidate.risk_flags = ip_flags

    if include_full_analysis:
        for candidate in candidates[:max_full_analysis]:
            whois_info = ssl_info = vt_info = None
            try:
                whois_info = whois_service.get_whois_info(candidate.variant)
            except Exception as exc:
                errors.append(f"WHOIS de {candidate.variant} falló: {exc}")
            try:
                ssl_info = ssl_service.get_ssl_info(candidate.variant)
            except Exception as exc:
                errors.append(f"SSL de {candidate.variant} falló: {exc}")
            try:
                vt_info = virustotal_service.get_virustotal_info(candidate.variant)
            except Exception as exc:
                errors.append(f"VirusTotal de {candidate.variant} falló: {exc}")

            abuseipdb_info = ip_reputation_cache.get(candidate.ip_address)
            flags, score = evaluate_risk(whois_info, ssl_info, vt_info, abuseipdb_info)
            candidate.risk_score = score
            candidate.risk_flags = flags
            candidate.fully_analyzed = True

    flags, score = evaluate_typosquatting_risk(candidates)

    case = TyposquattingCase(
        domain=domain,
        analyzed_at=datetime.now(timezone.utc),
        variants_generated=len(variant_pairs),
        resolved_count=len(candidates),
        candidates=[c.model_dump(mode="json") for c in candidates],
        risk_flags=[f.model_dump(mode="json") for f in flags],
        risk_score=score,
        errors=errors,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "typosquatting", case.id, integrity_payloads.typosquatting_payload(case))
    monitoring_service.touch_subject(db, "typosquatting", domain, case.id, score, flags)

    return case
