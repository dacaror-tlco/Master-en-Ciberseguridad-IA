"""
Servicio de correlación entre casos.

Cada módulo (dominio, email, wallet) analiza su propia pieza de forma
aislada. Este servicio busca coincidencias ENTRE módulos, que son señales
mucho más fuertes que cualquier señal individual: si el dominio que
analizaste por separado resulta ser justo el que usa el remitente de un
email sospechoso, ya no son "dos cosas sospechosas por separado", es la
misma infraestructura de una única estafa.
"""
from app.models.case import Case
from app.models.email_case import EmailCase
from app.models.typosquatting_case import TyposquattingCase
from app.models.wallet_case import WalletCase
from app.schemas.domain_analysis import RiskFlag


def find_correlations(
    domain_cases: list[Case],
    email_cases: list[EmailCase],
    wallet_cases: list[WalletCase],
    typosquatting_cases: list[TyposquattingCase] | None = None,
) -> list[RiskFlag]:
    typosquatting_cases = typosquatting_cases or []
    flags: list[RiskFlag] = []
    domain_names = {c.domain.lower() for c in domain_cases}

    for ec in email_cases:
        headers = ec.headers or {}
        from_address = headers.get("from_address") or ""
        if "@" not in from_address:
            continue
        sender_domain = from_address.rsplit("@", 1)[-1].lower()
        if sender_domain in domain_names:
            flags.append(RiskFlag(
                code="DOMAIN_MATCHES_EMAIL_SENDER",
                severity="high",
                description=(
                    f"El dominio '{sender_domain}' analizado en el módulo de dominios coincide "
                    f"con el remitente del email #{ec.id}: son parte de la misma infraestructura "
                    "de la estafa, no incidentes independientes."
                ),
            ))

    # Cruce: si una variante typosquatting activa coincide con el
    # remitente de un email, es una confirmación directa de que esa
    # variante concreta es la que se está usando para atacar, no solo un
    # dominio "aparcado" a la espera.
    active_variants = {
        c["variant"].lower()
        for tc in typosquatting_cases
        for c in (tc.candidates or [])
        if c.get("resolves")
    }
    for ec in email_cases:
        headers = ec.headers or {}
        from_address = headers.get("from_address") or ""
        if "@" not in from_address:
            continue
        sender_domain = from_address.rsplit("@", 1)[-1].lower()
        if sender_domain in active_variants:
            flags.append(RiskFlag(
                code="TYPOSQUATTING_VARIANT_USED_IN_EMAIL",
                severity="high",
                description=(
                    f"El remitente del email #{ec.id} ('{sender_domain}') es una de las variantes "
                    "typosquatting detectadas como activas: confirma que esa variante concreta ya "
                    "se está usando para atacar, no es solo un registro especulativo."
                ),
            ))

    return flags
