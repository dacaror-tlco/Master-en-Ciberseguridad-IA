"""
Motor de scoring de riesgo para emails.

Igual que en risk_engine.py (dominios), esta es la versión heurística de
la FASE 1. Reutilizamos el mismo esquema RiskFlag para que, más adelante,
un único modelo de IA pueda combinar señales de dominio + email + cripto
en un solo score consolidado por caso.

Combina cinco fuentes de señal, cada una opcional salvo las cabeceras:
1. Cabeceras (SPF/DKIM/DMARC, discrepancias remitente/responder-a/retorno,
   TLD, antigüedad del dominio) — solo si `is_raw_source` es True, porque
   sin el código fuente real no hay forma fiable de comprobar nada de esto.
2. Nombre visible del remitente vs. marca que dice representar.
3. Enlaces del cuerpo (acortadores, suplantación de marca, dominio muy
   nuevo, marcado por VirusTotal) — a partir de `EmailLinkInfo` ya
   enriquecido por `email_link_analysis.py`.
4. Adjuntos peligrosos (extensión ejecutable, doble extensión).
5. Reputación (AbuseIPDB) de la IP de origen extraída de la cabecera
   Received — reutiliza `ip_risk_engine.evaluate_ip_risk`, la misma
   fuente de verdad que usan los módulos de Dominio e IP, para no
   duplicar los umbrales de abuso en un tercer sitio.
"""
from app.schemas.domain_analysis import AbuseIpInfo, RiskFlag, WhoisInfo
from app.schemas.email_analysis import EmailAttachmentInfo, EmailHeaderInfo, EmailLinkInfo
from app.services import brand_dictionary
from app.services.ip_risk_engine import evaluate_ip_risk

_SUSPICIOUS_TLDS = {"xyz", "top", "tk", "gq", "ml", "cf", "work", "click", "loan"}


def _domain(address: str | None) -> str | None:
    if not address or "@" not in address:
        return None
    return address.rsplit("@", 1)[-1].lower()


def _evaluate_headers(headers: EmailHeaderInfo, sender_whois: WhoisInfo | None) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    from_domain = _domain(headers.from_address)
    reply_to_domain = _domain(headers.reply_to)
    return_path_domain = _domain(headers.return_path)

    # 1. Autenticación del remitente (la señal más fiable: es difícil de falsificar)
    if headers.spf_result == "fail":
        flags.append(RiskFlag(code="SPF_FAIL", severity="high",
                               description="El servidor no autoriza a este remitente a enviar en nombre de ese dominio (SPF fail)"))
        score += 35
    elif headers.spf_result in (None, "none"):
        flags.append(RiskFlag(code="SPF_MISSING", severity="low",
                               description="No se encontró verificación SPF en las cabeceras"))
        score += 10

    if headers.dkim_result == "fail":
        flags.append(RiskFlag(code="DKIM_FAIL", severity="high",
                               description="La firma criptográfica del email no es válida (DKIM fail): el contenido pudo ser alterado o el remitente es falso"))
        score += 30
    elif headers.dkim_result in (None, "none"):
        flags.append(RiskFlag(code="DKIM_MISSING", severity="low",
                               description="El email no está firmado digitalmente (sin DKIM)"))
        score += 10

    if headers.dmarc_result == "fail":
        flags.append(RiskFlag(code="DMARC_FAIL", severity="medium",
                               description="El email no cumple la política DMARC del dominio que dice ser el remitente"))
        score += 15

    # 2. Discrepancias entre direcciones (clásico truco: pedir que respondas a otro sitio)
    if reply_to_domain and from_domain and reply_to_domain != from_domain:
        flags.append(RiskFlag(
            code="REPLY_TO_MISMATCH", severity="medium",
            description=f"Las respuestas se redirigen a un dominio distinto del remitente ({headers.from_address} -> responde a {headers.reply_to})",
        ))
        score += 20

    if return_path_domain and from_domain and return_path_domain != from_domain:
        flags.append(RiskFlag(
            code="RETURN_PATH_MISMATCH", severity="low",
            description=f"El dominio de retorno de rebotes ({return_path_domain}) no coincide con el remitente ({from_domain})",
        ))
        score += 10

    # 3. TLD típico de campañas masivas/baratas de spam-phishing
    if from_domain and from_domain.rsplit(".", 1)[-1] in _SUSPICIOUS_TLDS:
        flags.append(RiskFlag(
            code="SUSPICIOUS_TLD", severity="low",
            description=f"El dominio del remitente usa una extensión ({from_domain.rsplit('.', 1)[-1]}) frecuente en campañas de phishing por su bajo coste",
        ))
        score += 10

    # 4. Antigüedad del dominio del remitente (reutilizamos el mismo criterio que en domain risk_engine)
    if sender_whois and sender_whois.domain_age_days is not None:
        if sender_whois.domain_age_days < 30:
            flags.append(RiskFlag(
                code="SENDER_DOMAIN_VERY_NEW", severity="high",
                description=f"El dominio del remitente se registró hace solo {sender_whois.domain_age_days} días",
            ))
            score += 30
        elif sender_whois.domain_age_days < 180:
            flags.append(RiskFlag(
                code="SENDER_DOMAIN_RECENT", severity="medium",
                description=f"El dominio del remitente tiene {sender_whois.domain_age_days} días de antigüedad",
            ))
            score += 10

    return flags, score


def _evaluate_display_name(headers: EmailHeaderInfo) -> tuple[list[RiskFlag], int]:
    """'Banco Seguro' <alguien@gmail.com> — el nombre visible dice ser una marca conocida
    pero el dominio real del remitente no le pertenece."""
    if not headers.from_display_name:
        return [], 0

    brand = brand_dictionary.find_mentioned_brand(headers.from_display_name)
    if not brand:
        return [], 0

    from_domain = _domain(headers.from_address)
    if from_domain and brand_dictionary.domain_belongs_to_brand(from_domain, brand):
        return [], 0

    return [RiskFlag(
        code="DISPLAY_NAME_BRAND_MISMATCH", severity="high",
        description=(
            f"El nombre visible del remitente ('{headers.from_display_name}') menciona la marca "
            f"'{brand}', pero la dirección real ({headers.from_address or 'desconocida'}) no pertenece a su dominio oficial"
        ),
    )], 35


def _evaluate_links(links: list[EmailLinkInfo]) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0
    flagged_domains: set[str] = set()

    for link in links:
        effective_domain = link.redirects_to or link.domain

        if link.is_shortener:
            flags.append(RiskFlag(
                code="SHORTENED_LINK", severity="medium",
                description=(
                    f"Enlace acortado ({link.domain}) que oculta el destino real"
                    + (f": {link.redirects_to}" if link.redirects_to else " (no se pudo resolver el destino)")
                ),
            ))
            score += 15

        if link.suspected_brand and effective_domain not in flagged_domains:
            flagged_domains.add(effective_domain)
            flags.append(RiskFlag(
                code="LINK_BRAND_IMPERSONATION", severity="high",
                description=f"Un enlace del cuerpo apunta a '{effective_domain}', que imita a la marca '{link.suspected_brand}' sin ser su dominio oficial",
            ))
            score += 30

        if link.domain_age_days is not None and link.domain_age_days < 30:
            flags.append(RiskFlag(
                code="LINK_DOMAIN_VERY_NEW", severity="high",
                description=f"El dominio de un enlace del cuerpo ('{effective_domain}') se registró hace solo {link.domain_age_days} días",
            ))
            score += 25

        if link.virustotal_malicious_count:
            flags.append(RiskFlag(
                code="LINK_FLAGGED_BY_VIRUSTOTAL", severity="high",
                description=f"{link.virustotal_malicious_count} motores de VirusTotal marcan '{effective_domain}' como malicioso",
            ))
            score += 35

    return flags, score


def _evaluate_attachments(attachments: list[EmailAttachmentInfo]) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    for attachment in attachments:
        if attachment.is_dangerous_extension:
            flags.append(RiskFlag(
                code="DANGEROUS_ATTACHMENT", severity="high",
                description=f"El adjunto '{attachment.filename}' tiene una extensión (.{attachment.extension}) capaz de ejecutar código al abrirlo",
            ))
            score += 35

        if attachment.has_double_extension:
            flags.append(RiskFlag(
                code="DOUBLE_EXTENSION_ATTACHMENT", severity="high",
                description=f"El adjunto '{attachment.filename}' usa una doble extensión, técnica clásica para disfrazar un ejecutable de documento",
            ))
            score += 25

    return flags, score


def evaluate_email_risk(
    headers: EmailHeaderInfo,
    sender_whois: WhoisInfo | None,
    links: list[EmailLinkInfo] | None = None,
    attachments: list[EmailAttachmentInfo] | None = None,
    is_raw_source: bool = True,
    originating_ip_abuseipdb: AbuseIpInfo | None = None,
) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if is_raw_source:
        header_flags, header_score = _evaluate_headers(headers, sender_whois)
        flags += header_flags
        score += header_score
    else:
        # Sin código fuente real no hay SPF/DKIM/DMARC/Received que comprobar
        # — mejor decirlo claramente que rellenar de flags "_MISSING" que
        # suenan a que sí se comprobó y faltaba, cuando en realidad no había
        # nada que comprobar.
        flags.append(RiskFlag(
            code="LIMITED_ANALYSIS_NO_RAW_SOURCE", severity="low",
            description=(
                "El texto proporcionado no es el código fuente original del email (no se encontraron "
                "cabeceras técnicas como Received o Authentication-Results), así que no se pudo verificar "
                "SPF/DKIM/DMARC ni la ruta de servidores. El análisis se basa en el contenido: enlaces, "
                "adjuntos y nombre del remitente."
            ),
        ))

    display_flags, display_score = _evaluate_display_name(headers)
    flags += display_flags
    score += display_score

    if links:
        link_flags, link_score = _evaluate_links(links)
        flags += link_flags
        score += link_score

    if attachments:
        attachment_flags, attachment_score = _evaluate_attachments(attachments)
        flags += attachment_flags
        score += attachment_score

    if originating_ip_abuseipdb:
        ip_flags, ip_score = evaluate_ip_risk(originating_ip_abuseipdb)
        flags += ip_flags
        score += ip_score

    return flags, min(score, 100)
