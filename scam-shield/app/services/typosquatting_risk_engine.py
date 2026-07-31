"""
Motor de scoring de riesgo para el módulo de typosquatting.

A diferencia de los otros motores, aquí no evaluamos "¿es sospechoso este
dominio?" sino "¿cuánta suplantación activa hay alrededor de esta marca?".
Es un score de EXPOSICIÓN, no de un objetivo único.

Cada variante activa puede tener `risk_score` de dos orígenes distintos
(ver `TyposquattingCandidate.fully_analyzed`): análisis completo
(WHOIS/SSL/VirusTotal, caro y limitado a unas pocas variantes) o solo
reputación de su IP (AbuseIPDB, barato, se aplica a todas las variantes
activas). Se tratan como señales separadas — un score alto por IP sola es
más débil (podría ser hosting compartido) que uno por análisis completo.
"""
from app.schemas.domain_analysis import RiskFlag
from app.schemas.typosquatting import TyposquattingCandidate


def evaluate_typosquatting_risk(candidates: list[TyposquattingCandidate]) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    resolved = [c for c in candidates if c.resolves]
    count = len(resolved)

    if count == 0:
        return flags, 0

    if count >= 6:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_HIGH_VOLUME", severity="high",
            description=f"Se han encontrado {count} dominios activos que imitan la marca — indica una campaña de suplantación organizada, no casos aislados",
        ))
        score += 50
    elif count >= 3:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_MODERATE_VOLUME", severity="medium",
            description=f"Se han encontrado {count} dominios activos que imitan la marca",
        ))
        score += 25
    else:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_LOW_VOLUME", severity="low",
            description=f"Se han encontrado {count} dominio(s) activo(s) que imitan la marca",
        ))
        score += 10

    analyzed_with_ssl = [c for c in resolved if any(f.code == "CERT_JUST_ISSUED" for f in c.risk_flags)]
    if analyzed_with_ssl:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_ACTIVELY_WEAPONIZED", severity="high",
            description=(
                f"{len(analyzed_with_ssl)} de las variantes activas tienen certificado SSL recién emitido: "
                "no son solo dominios aparcados, están siendo preparados o ya usados para atacar"
            ),
        ))
        score += 30

    # Separado por `fully_analyzed`: un risk_score alto puede venir del
    # análisis completo (WHOIS/SSL/VirusTotal) o solo de la reputación de
    # la IP a la que resuelve (AbuseIPDB, más barato pero también más
    # débil como señal — la IP podría ser hosting compartido).
    high_full_risk = [c for c in resolved if c.fully_analyzed and c.risk_score is not None and c.risk_score >= 60]
    if high_full_risk:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_HIGH_RISK_VARIANT", severity="high",
            description=f"{len(high_full_risk)} variante(s) analizada(s) en profundidad tienen su propio score de riesgo alto (≥60/100)",
        ))
        score += 20

    high_ip_only_risk = [c for c in resolved if not c.fully_analyzed and c.risk_score is not None and c.risk_score >= 60]
    if high_ip_only_risk:
        flags.append(RiskFlag(
            code="TYPOSQUATTING_VARIANT_ON_ABUSIVE_IP", severity="medium",
            description=(
                f"{len(high_ip_only_risk)} variante(s) activa(s) están alojadas en una IP con reputación "
                "de abuso alta (AbuseIPDB), aunque no se hayan analizado en profundidad — más débil que "
                "un análisis completo (podría ser hosting compartido), pero indicativo"
            ),
        ))
        score += 15

    return flags, min(score, 100)
