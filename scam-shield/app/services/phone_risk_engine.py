"""
Motor de scoring de riesgo para teléfonos.

A diferencia del dominio/email/wallet, aquí no hay "antigüedad" ni
"histórico de movimientos" — la señal principal es el TIPO DE LÍNEA:

- PREMIUM_RATE: tarificación especial, cobra por llamada/minuto. Es el
  mecanismo económico detrás del clásico timo de "has ganado un premio,
  llama a este número" o las llamadas perdidas que invitan a devolver
  la llamada ("wangiri").
- VOIP: número virtual, se puede crear y desechar en segundos, sin
  necesidad de una línea física ni contrato — habitual en campañas de
  estafa a gran escala precisamente por lo barato y anónimo que es.
- Formato inválido: puede indicar un número falsificado o mal formado
  a propósito (spoofing de identificador de llamada).
- Reportes comunitarios (OpenSpam): si otras personas ya han marcado
  este número concreto como fraude/spam, es la señal más directa de
  todas — no es una inferencia nuestra, es la experiencia real de otras
  víctimas con ese mismo número.
- Puntuación de fraude (IPQualityScore, opcional): señales de
  comportamiento agregado (VOIP/prepago, abuso reciente, filtrado en una
  brecha de datos) — nunca la identidad del titular, ver
  ipqualityscore_service.py.
- Carrier en tiempo real (Twilio Lookup, opcional y de pago): detecta
  VoIP/portabilidad que la detección offline (basada en rangos estáticos
  de numeración) no puede ver.
"""
from app.schemas.domain_analysis import RiskFlag
from app.schemas.phone_analysis import CarrierIntelligenceInfo, CommunityReportInfo, FraudScoreInfo, PhoneInfo

_HIGH_DANGER_LEVELS = {"alto", "high", "critico", "crítico"}
_MEDIUM_DANGER_LEVELS = {"medio", "medium", "moderado"}
_HIGH_FRAUD_SCORE_THRESHOLD = 85
_MODERATE_FRAUD_SCORE_THRESHOLD = 60


def evaluate_phone_risk(
    phone_info: PhoneInfo,
    community_info: CommunityReportInfo | None = None,
    fraud_info: FraudScoreInfo | None = None,
    carrier_intel: CarrierIntelligenceInfo | None = None,
) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if not phone_info.is_valid:
        flags.append(RiskFlag(
            code="PHONE_INVALID_FORMAT", severity="medium",
            description="El número no tiene un formato válido para su país — puede estar falsificado o mal formado a propósito",
        ))
        score += 20

    if phone_info.line_type == "PREMIUM_RATE":
        flags.append(RiskFlag(
            code="PHONE_PREMIUM_RATE", severity="high",
            description="Es un número de tarificación especial (cobra por llamada/minuto) — mecanismo económico habitual en timos de 'falso premio' o llamadas perdidas ('wangiri')",
        ))
        score += 50

    elif phone_info.line_type == "VOIP":
        flags.append(RiskFlag(
            code="PHONE_VOIP", severity="medium",
            description="Es un número VoIP: se puede crear y desechar en segundos sin línea física ni contrato — habitual en campañas de estafa a gran escala",
        ))
        score += 20

    elif phone_info.line_type == "PAGER":
        flags.append(RiskFlag(
            code="PHONE_PAGER", severity="low",
            description="Tipo de línea muy poco común hoy en día (buscapersonas) — no es necesariamente sospechoso, pero es inusual",
        ))
        score += 5

    elif phone_info.line_type == "UNKNOWN" and phone_info.is_valid:
        flags.append(RiskFlag(
            code="PHONE_UNKNOWN_LINE_TYPE", severity="low",
            description="No se ha podido determinar el tipo de línea, a pesar de tener un formato válido",
        ))
        score += 10

    if community_info and community_info.reports_count > 0:
        danger = (community_info.danger_level or "").lower()
        category = community_info.category or "actividad no deseada"
        count = community_info.reports_count

        if danger in _HIGH_DANGER_LEVELS or count >= 20:
            flags.append(RiskFlag(
                code="PHONE_COMMUNITY_REPORTED_HIGH", severity="high",
                description=f"{count} personas han reportado este número por '{category}' — nivel de peligro marcado como alto por la comunidad",
            ))
            score += 45
        elif danger in _MEDIUM_DANGER_LEVELS or count >= 5:
            flags.append(RiskFlag(
                code="PHONE_COMMUNITY_REPORTED_MEDIUM", severity="medium",
                description=f"{count} personas han reportado este número por '{category}'",
            ))
            score += 25
        else:
            flags.append(RiskFlag(
                code="PHONE_COMMUNITY_REPORTED_LOW", severity="low",
                description=f"{count} reporte(s) de '{category}' asociado(s) a este número",
            ))
            score += 10

    if fraud_info:
        if fraud_info.fraud_score is not None and fraud_info.fraud_score >= _HIGH_FRAUD_SCORE_THRESHOLD:
            flags.append(RiskFlag(
                code="PHONE_HIGH_FRAUD_SCORE", severity="high",
                description=f"IPQualityScore le da a este número una puntuación de fraude de {fraud_info.fraud_score}/100 (muy alta)",
            ))
            score += 40
        elif fraud_info.fraud_score is not None and fraud_info.fraud_score >= _MODERATE_FRAUD_SCORE_THRESHOLD:
            flags.append(RiskFlag(
                code="PHONE_MODERATE_FRAUD_SCORE", severity="medium",
                description=f"IPQualityScore le da a este número una puntuación de fraude de {fraud_info.fraud_score}/100 (moderada)",
            ))
            score += 20

        if fraud_info.recent_abuse:
            flags.append(RiskFlag(
                code="PHONE_RECENT_ABUSE_REPORTED", severity="high",
                description="IPQualityScore registra abuso reciente asociado a este número (spam/fraude reportado activamente)",
            ))
            score += 35

        if fraud_info.leaked:
            flags.append(RiskFlag(
                code="PHONE_NUMBER_LEAKED", severity="low",
                description=(
                    "Este número aparece en alguna brecha de datos filtrada — muy común y no concluyente "
                    "por sí solo (les pasa a millones de números), pero se anota igualmente"
                ),
            ))
            score += 5

    if carrier_intel and carrier_intel.line_type and (carrier_intel.line_type or "").lower() == "voip" \
            and phone_info.line_type not in ("VOIP", "PREMIUM_RATE"):
        flags.append(RiskFlag(
            code="PHONE_VOIP_LIVE_MISMATCH", severity="high",
            description=(
                f"El operador en tiempo real (Twilio) indica que este número es VoIP, aunque la "
                f"detección offline lo clasificó como '{phone_info.line_type}' — indicio de número "
                "portado o VoIP moderno no catalogado en la base de datos estática, más fiable que la "
                "detección offline porque consulta al operador en el momento"
            ),
        ))
        score += 30

    return flags, min(score, 100)
