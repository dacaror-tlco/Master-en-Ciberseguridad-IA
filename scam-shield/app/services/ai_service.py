"""
Capa de IA: narrativa explicativa del caso consolidado.

Las heurísticas de los módulos anteriores ya resuelven el "qué" (los
scores y las señales de riesgo, de forma determinista y explicable por
regla). Esta capa añade el "por qué en palabras humanas": un LLM redacta
un párrafo en español claro, cruzando las señales de los distintos
módulos, pensado para alguien no técnico (la víctima, o quien reciba la
denuncia).

Deliberadamente NO delegamos el score en el LLM: los números siguen
saliendo de las reglas deterministas (reproducibles, auditables, sin
alucinaciones). El LLM solo redacta la explicación en base a los datos
que le pasamos — no se le pide "que decida" nada, solo que lo explique.

Si no hay ANTHROPIC_API_KEY configurada, el resto del sistema sigue
funcionando exactamente igual: esta capa es un extra, no una dependencia.
"""
from anthropic import Anthropic

from app.core.config import settings
from app.models.case import Case
from app.models.email_case import EmailCase
from app.models.wallet_case import WalletCase
from app.schemas.domain_analysis import RiskFlag

# Cualquier modelo Claude disponible en tu cuenta sirve; este es un buen
# equilibrio entre calidad y coste para un texto corto como este.
_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = (
    "Eres un analista de ciberseguridad redactando la sección explicativa de un informe de "
    "posible fraude, para adjuntar a una denuncia policial. Te paso los datos técnicos que ya "
    "se han extraído de forma automática (dominio, email y/o wallet cripto involucrados). "
    "Escribe UN SOLO PÁRRAFO en español, claro y sin jerga innecesaria, dirigido a alguien no "
    "técnico, explicando por qué este caso presenta indicios de fraude, citando los datos "
    "concretos más relevantes. No inventes ningún dato que no esté en la información "
    "proporcionada. No uses listas ni encabezados, solo el párrafo."
)


def _build_case_summary(
    domain_cases: list[Case],
    email_cases: list[EmailCase],
    wallet_cases: list[WalletCase],
    correlation_flags: list[RiskFlag],
    victim_notes: str | None,
) -> str:
    lines: list[str] = []

    for c in domain_cases:
        codes = [f["code"] for f in (c.risk_flags or [])]
        vt = c.virustotal or {}
        vt_note = f", VirusTotal: {vt.get('malicious_count', 0)} motores lo marcan malicioso" if vt else ""
        lines.append(f"- Dominio '{c.domain}': score de riesgo {c.risk_score}/100. Señales: {codes or 'ninguna'}{vt_note}.")

    for c in email_cases:
        from_address = (c.headers or {}).get("from_address")
        codes = [f["code"] for f in (c.risk_flags or [])]
        lines.append(f"- Email de '{from_address}' (asunto: '{c.subject}'): score {c.risk_score}/100. Señales: {codes or 'ninguna'}.")

    for c in wallet_cases:
        codes = [f["code"] for f in (c.risk_flags or [])]
        lines.append(f"- Wallet '{c.address}' ({c.chain}): score {c.risk_score}/100. Señales: {codes or 'ninguna'}.")

    if correlation_flags:
        for f in correlation_flags:
            lines.append(f"- Correlación detectada entre módulos: {f.description}")

    if victim_notes:
        lines.append(f"- Relato de la persona afectada: {victim_notes}")

    return "\n".join(lines)


_EMAIL_SYSTEM_PROMPT = (
    "Eres un analista de ciberseguridad explicando a la víctima de un posible fraude por email, en "
    "shock y sin conocimientos técnicos, qué se ha encontrado en el análisis automático de ese email. "
    "Te paso los datos técnicos ya extraídos (cabeceras, enlaces del cuerpo, adjuntos, señales de "
    "riesgo). Escribe UN SOLO PÁRRAFO breve en español, claro y tranquilizador en el tono pero firme en "
    "el contenido, explicando en qué basas la conclusión y qué debería evitar hacer la víctima (no "
    "pulsar enlaces, no abrir adjuntos, no responder...) si el riesgo es alto. No inventes ningún dato "
    "que no esté en la información proporcionada. No uses listas ni encabezados, solo el párrafo."
)


def _build_email_summary(case: EmailCase) -> str:
    headers = case.headers or {}
    lines = [
        f"- Remitente: {headers.get('from_address')} (nombre mostrado: {headers.get('from_display_name')})",
        f"- Asunto: {headers.get('subject')}",
        f"- SPF: {headers.get('spf_result')}, DKIM: {headers.get('dkim_result')}, DMARC: {headers.get('dmarc_result')}",
        f"- Score de riesgo: {case.risk_score}/100",
    ]

    if case.is_raw_source is False:
        lines.append("- No se pudo verificar el código fuente técnico del email (el usuario pegó solo el texto visible).")

    codes = [f["code"] for f in (case.risk_flags or [])]
    lines.append(f"- Señales detectadas: {codes or 'ninguna'}")

    for f in (case.risk_flags or []):
        lines.append(f"  · {f['code']}: {f['description']}")

    if case.links:
        suspicious_links = [l for l in case.links if l.get("suspected_brand") or l.get("virustotal_malicious_count") or l.get("is_shortener")]
        if suspicious_links:
            lines.append(f"- Enlaces sospechosos en el cuerpo: {len(suspicious_links)} de {len(case.links)} enlaces totales")

    if case.attachments:
        dangerous = [a for a in case.attachments if a.get("is_dangerous_extension") or a.get("has_double_extension")]
        lines.append(f"- Adjuntos: {len(case.attachments)} en total" + (f", {len(dangerous)} con extensión peligrosa" if dangerous else ""))

    return "\n".join(lines)


def generate_email_narrative(case: EmailCase) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "No hay ANTHROPIC_API_KEY configurada. Consigue una en https://console.anthropic.com "
            "y añádela a tu archivo .env"
        )

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=_MODEL,
        max_tokens=350,
        system=_EMAIL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_email_summary(case)}],
    )

    return "".join(block.text for block in response.content if block.type == "text").strip()


def generate_narrative(
    domain_cases: list[Case],
    email_cases: list[EmailCase],
    wallet_cases: list[WalletCase],
    correlation_flags: list[RiskFlag],
    victim_notes: str | None = None,
) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "No hay ANTHROPIC_API_KEY configurada. Consigue una en https://console.anthropic.com "
            "y añádela a tu archivo .env"
        )

    case_summary = _build_case_summary(domain_cases, email_cases, wallet_cases, correlation_flags, victim_notes)

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=_MODEL,
        max_tokens=500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": case_summary}],
    )

    return "".join(block.text for block in response.content if block.type == "text").strip()
