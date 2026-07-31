"""
Motor de scoring de riesgo para IPs — única fuente de verdad para la señal
de AbuseIPDB, reutilizada tanto por el módulo de dominio (IP a la que
resuelve) como por el módulo de IP, para no duplicar los mismos umbrales
en dos sitios.
"""
from app.schemas.domain_analysis import AbuseIpInfo, RiskFlag

_HIGH_ABUSE_THRESHOLD = 75
_MODERATE_ABUSE_THRESHOLD = 25


def evaluate_ip_risk(abuseipdb_info: AbuseIpInfo | None) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if not abuseipdb_info:
        return flags, score

    if abuseipdb_info.abuse_confidence_score >= _HIGH_ABUSE_THRESHOLD:
        flags.append(RiskFlag(
            code="IP_HIGH_ABUSE_SCORE", severity="high",
            description=f"AbuseIPDB le da a esta IP una puntuación de abuso de {abuseipdb_info.abuse_confidence_score}/100 (muy alta), con {abuseipdb_info.total_reports} reporte(s)",
        ))
        score += 40
    elif abuseipdb_info.abuse_confidence_score >= _MODERATE_ABUSE_THRESHOLD:
        flags.append(RiskFlag(
            code="IP_MODERATE_ABUSE_SCORE", severity="medium",
            description=f"AbuseIPDB le da a esta IP una puntuación de abuso de {abuseipdb_info.abuse_confidence_score}/100 (moderada), con {abuseipdb_info.total_reports} reporte(s)",
        ))
        score += 20

    if abuseipdb_info.is_tor:
        flags.append(RiskFlag(
            code="IP_TOR_EXIT_NODE", severity="low",
            description="Esta IP es un nodo de salida de Tor — lo usa gente legítima también, no es concluyente por sí solo, pero se anota",
        ))
        score += 5

    return flags, min(score, 100)
