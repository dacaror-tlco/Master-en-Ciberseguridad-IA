from datetime import datetime, timezone

from app.models.case import Case
from app.models.email_case import EmailCase
from app.services.correlation_service import find_correlations


def _domain_case(domain: str) -> Case:
    return Case(id=1, domain=domain, risk_score=50, analyzed_at=datetime.now(timezone.utc))


def _email_case(from_address: str) -> EmailCase:
    return EmailCase(
        id=1, from_address=from_address, risk_score=50,
        headers={"from_address": from_address}, analyzed_at=datetime.now(timezone.utc),
    )


def test_detecta_coincidencia_entre_dominio_y_remitente():
    domain_cases = [_domain_case("banco-falso.xyz")]
    email_cases = [_email_case("soporte@banco-falso.xyz")]
    flags = find_correlations(domain_cases, email_cases, [])
    assert len(flags) == 1
    assert flags[0].code == "DOMAIN_MATCHES_EMAIL_SENDER"
    assert flags[0].severity == "high"


def test_no_hay_falsos_positivos_con_dominios_distintos():
    domain_cases = [_domain_case("banco-falso.xyz")]
    email_cases = [_email_case("soporte@otro-dominio-sin-relacion.com")]
    flags = find_correlations(domain_cases, email_cases, [])
    assert flags == []


def test_variante_typosquatting_activa_usada_como_remitente_de_email():
    from app.models.typosquatting_case import TyposquattingCase

    typo_case = TyposquattingCase(
        id=1, domain="banco-real.com", risk_score=30,
        candidates=[{"variant": "banc0-real.com", "technique": "homoglyph", "resolves": True, "ip_address": "1.2.3.4", "risk_score": None, "risk_flags": []}],
        analyzed_at=datetime.now(timezone.utc),
    )
    email_cases = [_email_case("soporte@banc0-real.com")]

    flags = find_correlations([], email_cases, [], [typo_case])
    assert len(flags) == 1
    assert flags[0].code == "TYPOSQUATTING_VARIANT_USED_IN_EMAIL"


def test_variante_typosquatting_no_resuelta_no_correlaciona():
    from app.models.typosquatting_case import TyposquattingCase

    typo_case = TyposquattingCase(
        id=1, domain="banco-real.com", risk_score=0,
        candidates=[{"variant": "banc0-real.com", "technique": "homoglyph", "resolves": False, "ip_address": None, "risk_score": None, "risk_flags": []}],
        analyzed_at=datetime.now(timezone.utc),
    )
    email_cases = [_email_case("soporte@banc0-real.com")]

    flags = find_correlations([], email_cases, [], [typo_case])
    assert flags == []


def test_sin_casos_no_hay_correlaciones():
    assert find_correlations([], [], []) == []


def test_comparacion_de_dominios_no_distingue_mayusculas():
    domain_cases = [_domain_case("Banco-Falso.XYZ")]
    email_cases = [_email_case("soporte@banco-falso.xyz")]
    flags = find_correlations(domain_cases, email_cases, [])
    assert len(flags) == 1
