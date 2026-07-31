"""
Motor de scoring de riesgo.

Esta es la versión FASE 1: reglas simples y explicables a mano.
En la FASE 3 del proyecto, sustituiremos (o combinaremos) esto por un
modelo entrenado, pero mantenemos la misma interfaz de salida
(lista de RiskFlag + risk_score) para no romper el resto del sistema.

Diseñarlo así desde ya es importante para el TFM: puedes comparar
"antes de IA" (esta heurística) vs "con IA" (fase 3) sobre el mismo
conjunto de casos, y eso es una sección de evaluación muy sólida.
"""
from app.schemas.domain_analysis import (
    AbuseIpInfo,
    CrtShInfo,
    DnsRecords,
    IpReputationEntry,
    RiskFlag,
    SSLCertInfo,
    VirusTotalInfo,
    WaybackInfo,
    WhoisInfo,
)
from app.services.ip_risk_engine import evaluate_ip_risk

# Margen sobre la fecha de registro WHOIS: un primer snapshot unos pocos
# días antes de la fecha de creación es ruido normal (desfases de reloj
# entre fuentes, o el crawler pasó justo el día del registro), no señal.
_DOMAIN_REUSE_MIN_GAP_DAYS = 30


def _evaluate_dns(dns_info: DnsRecords | None) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0
    if not dns_info or not dns_info.mx_hosts:
        # Sin MX no hay "postura de seguridad de correo" que evaluar — un
        # dominio que no recibe email no necesita SPF/DMARC.
        return flags, score

    if not dns_info.has_spf:
        flags.append(RiskFlag(
            code="DOMAIN_NO_SPF", severity="low",
            description="El dominio recibe correo (tiene MX) pero no tiene SPF configurado en su propio DNS: cualquiera podría enviar emails falsificando este remitente",
        ))
        score += 5

    if not dns_info.has_dmarc:
        flags.append(RiskFlag(
            code="DOMAIN_NO_DMARC", severity="low",
            description="El dominio no tiene política DMARC configurada: no protege a terceros de que se falsifique su nombre como remitente",
        ))
        score += 5

    return flags, score


def _evaluate_additional_ips(ip_reputations: list[IpReputationEntry], primary_ip: str | None) -> tuple[list[RiskFlag], int]:
    """
    La IP principal (`resolved_ip`/`abuseipdb`) ya se evalúa más abajo — aquí
    solo las IPs EXTRA que resuelve el dominio (balanceo, CDN, u otras IPs
    sospechosas que no salieron como la principal), para no contar dos veces
    la misma señal. Los códigos llevan el prefijo ADDITIONAL_ y la IP en la
    descripción para no confundirse con la señal de la IP principal.
    """
    flags: list[RiskFlag] = []
    score = 0
    for entry in ip_reputations:
        if entry.ip == primary_ip or not entry.abuseipdb:
            continue
        ip_flags, ip_score = evaluate_ip_risk(entry.abuseipdb)
        for f in ip_flags:
            flags.append(RiskFlag(code=f"ADDITIONAL_{f.code}", severity=f.severity, description=f"[{entry.ip}] {f.description}"))
        score += ip_score
    return flags, score


def _evaluate_crtsh(crtsh_info: CrtShInfo | None) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0
    if crtsh_info and crtsh_info.suspected_brand_subdomains:
        subdomains = ", ".join(crtsh_info.suspected_brand_subdomains[:5])
        flags.append(RiskFlag(
            code="SUBDOMAIN_BRAND_IMPERSONATION", severity="high",
            description=f"Se ha emitido certificado para subdominio(s) que mencionan una marca conocida sin pertenecerle: {subdomains}",
        ))
        score += 30
    return flags, score


def _evaluate_wayback(wayback_info: WaybackInfo | None, whois_info: WhoisInfo | None) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0
    if not wayback_info:
        return flags, score

    if wayback_info.total_snapshots == 0:
        flags.append(RiskFlag(
            code="DOMAIN_NEVER_ARCHIVED", severity="low",
            description="El dominio nunca ha sido archivado por Wayback Machine — normal en uno recién creado, refuerza otras señales de novedad",
        ))
        score += 5
    elif (
        wayback_info.first_snapshot
        and whois_info
        and whois_info.creation_date
        and (whois_info.creation_date - wayback_info.first_snapshot).days > _DOMAIN_REUSE_MIN_GAP_DAYS
    ):
        flags.append(RiskFlag(
            code="DOMAIN_REUSED_AFTER_EXPIRY", severity="high",
            description=(
                f"Wayback Machine tiene una captura de este dominio desde {wayback_info.first_snapshot.date()}, "
                f"muy anterior a su fecha de registro WHOIS actual ({whois_info.creation_date.date()}): "
                "probablemente es un dominio expirado y vuelto a registrar para heredar su reputación/histórico"
            ),
        ))
        score += 35

    return flags, score


def evaluate_risk(
    whois_info: WhoisInfo | None,
    ssl_info: SSLCertInfo | None,
    vt_info: VirusTotalInfo | None = None,
    abuseipdb_info: AbuseIpInfo | None = None,
    dns_info: DnsRecords | None = None,
    ip_reputations: list[IpReputationEntry] | None = None,
    crtsh_info: CrtShInfo | None = None,
    wayback_info: WaybackInfo | None = None,
    resolved_ip: str | None = None,
) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if whois_info and whois_info.domain_age_days is not None:
        if whois_info.domain_age_days < 30:
            flags.append(RiskFlag(
                code="DOMAIN_VERY_NEW",
                description=f"El dominio se registró hace solo {whois_info.domain_age_days} días",
                severity="high",
            ))
            score += 40
        elif whois_info.domain_age_days < 180:
            flags.append(RiskFlag(
                code="DOMAIN_RECENT",
                description=f"El dominio tiene {whois_info.domain_age_days} días de antigüedad",
                severity="medium",
            ))
            score += 15

    if whois_info and not whois_info.registrar:
        flags.append(RiskFlag(
            code="WHOIS_HIDDEN",
            description="No se ha podido obtener el registrador (posible privacidad WHOIS agresiva)",
            severity="low",
        ))
        score += 5

    if ssl_info:
        if not ssl_info.has_valid_cert:
            flags.append(RiskFlag(
                code="NO_VALID_SSL",
                description="El dominio no presenta un certificado SSL válido",
                severity="high",
            ))
            score += 30
        elif ssl_info.days_since_issued is not None and ssl_info.days_since_issued < 7:
            flags.append(RiskFlag(
                code="CERT_JUST_ISSUED",
                description=f"El certificado SSL se emitió hace {ssl_info.days_since_issued} días",
                severity="medium",
            ))
            score += 20

    if vt_info:
        if vt_info.malicious_count >= 5:
            flags.append(RiskFlag(
                code="VT_HIGH_DETECTION",
                description=f"{vt_info.malicious_count} motores de seguridad en VirusTotal marcan este dominio como malicioso",
                severity="high",
            ))
            score += 40
        elif vt_info.malicious_count >= 1:
            flags.append(RiskFlag(
                code="VT_SOME_DETECTION",
                description=f"{vt_info.malicious_count} motor(es) de seguridad en VirusTotal marcan este dominio como malicioso",
                severity="medium",
            ))
            score += 20

        if vt_info.suspicious_count >= 1:
            flags.append(RiskFlag(
                code="VT_SUSPICIOUS_VOTES",
                description=f"{vt_info.suspicious_count} motor(es) en VirusTotal marcan este dominio como sospechoso (sin llegar a malicioso)",
                severity="low",
            ))
            score += 10

    ip_flags, ip_score = evaluate_ip_risk(abuseipdb_info)
    flags += ip_flags
    score += ip_score

    dns_flags, dns_score = _evaluate_dns(dns_info)
    flags += dns_flags
    score += dns_score

    additional_ip_flags, additional_ip_score = _evaluate_additional_ips(ip_reputations or [], resolved_ip)
    flags += additional_ip_flags
    score += additional_ip_score

    crtsh_flags, crtsh_score = _evaluate_crtsh(crtsh_info)
    flags += crtsh_flags
    score += crtsh_score

    wayback_flags, wayback_score = _evaluate_wayback(wayback_info, whois_info)
    flags += wayback_flags
    score += wayback_score

    return flags, min(score, 100)
