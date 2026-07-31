from app.schemas.domain_analysis import RiskFlag
from app.schemas.typosquatting import TyposquattingCandidate
from app.services.typosquatting_risk_engine import evaluate_typosquatting_risk


def _candidate(variant="fake.com", resolves=True, risk_score=None, risk_flags=None, fully_analyzed=False) -> TyposquattingCandidate:
    return TyposquattingCandidate(
        variant=variant, technique="omission", resolves=resolves,
        risk_score=risk_score, risk_flags=risk_flags or [], fully_analyzed=fully_analyzed,
    )


def test_sin_variantes_resueltas_score_cero():
    flags, score = evaluate_typosquatting_risk([])
    assert score == 0
    assert flags == []


def test_una_variante_resuelta_es_severidad_baja():
    flags, score = evaluate_typosquatting_risk([_candidate()])
    assert "TYPOSQUATTING_LOW_VOLUME" in [f.code for f in flags]
    assert score == 10


def test_varias_variantes_es_severidad_media():
    candidates = [_candidate(f"fake{i}.com") for i in range(3)]
    flags, score = evaluate_typosquatting_risk(candidates)
    assert "TYPOSQUATTING_MODERATE_VOLUME" in [f.code for f in flags]


def test_muchas_variantes_es_severidad_alta():
    candidates = [_candidate(f"fake{i}.com") for i in range(8)]
    flags, score = evaluate_typosquatting_risk(candidates)
    codes = [f.code for f in flags]
    assert "TYPOSQUATTING_HIGH_VOLUME" in codes
    assert score >= 50


def test_certificado_recien_emitido_dispara_weaponized():
    cert_flag = RiskFlag(code="CERT_JUST_ISSUED", severity="medium", description="test")
    candidates = [_candidate(risk_flags=[cert_flag])]
    flags, score = evaluate_typosquatting_risk(candidates)
    assert "TYPOSQUATTING_ACTIVELY_WEAPONIZED" in [f.code for f in flags]


def test_variante_con_score_alto_completo_dispara_flag():
    candidates = [_candidate(risk_score=75, fully_analyzed=True)]
    flags, _ = evaluate_typosquatting_risk(candidates)
    assert "TYPOSQUATTING_HIGH_RISK_VARIANT" in [f.code for f in flags]
    assert "TYPOSQUATTING_VARIANT_ON_ABUSIVE_IP" not in [f.code for f in flags]


def test_variante_con_score_alto_solo_ip_dispara_flag_mas_debil():
    """Regresión: un score alto que viene SOLO de la reputación de IP (AbuseIPDB), sin
    análisis completo, es una señal más débil — no debe contar como TYPOSQUATTING_HIGH_RISK_VARIANT."""
    candidates = [_candidate(risk_score=75, fully_analyzed=False)]
    flags, score = evaluate_typosquatting_risk(candidates)
    assert "TYPOSQUATTING_VARIANT_ON_ABUSIVE_IP" in [f.code for f in flags]
    assert "TYPOSQUATTING_HIGH_RISK_VARIANT" not in [f.code for f in flags]
    assert score == 25  # 10 (low volume, 1 variante) + 15 (IP abusiva)


def test_score_nunca_supera_100():
    cert_flag = RiskFlag(code="CERT_JUST_ISSUED", severity="medium", description="test")
    candidates = [_candidate(f"fake{i}.com", risk_score=90, risk_flags=[cert_flag], fully_analyzed=True) for i in range(10)]
    _, score = evaluate_typosquatting_risk(candidates)
    assert score <= 100
