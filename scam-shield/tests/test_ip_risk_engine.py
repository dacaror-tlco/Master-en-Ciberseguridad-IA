from app.schemas.domain_analysis import AbuseIpInfo
from app.services.ip_risk_engine import evaluate_ip_risk


def test_sin_info_no_dispara_nada():
    flags, score = evaluate_ip_risk(None)
    assert flags == []
    assert score == 0


def test_score_bajo_no_dispara_nada():
    info = AbuseIpInfo(ip_address="1.2.3.4", abuse_confidence_score=5)
    flags, score = evaluate_ip_risk(info)
    assert flags == []
    assert score == 0


def test_score_moderado_dispara_flag_medio():
    info = AbuseIpInfo(ip_address="1.2.3.4", abuse_confidence_score=50, total_reports=3)
    flags, score = evaluate_ip_risk(info)
    flag = next(f for f in flags if f.code == "IP_MODERATE_ABUSE_SCORE")
    assert flag.severity == "medium"
    assert score >= 20


def test_score_alto_dispara_flag_alto():
    info = AbuseIpInfo(ip_address="1.2.3.4", abuse_confidence_score=90, total_reports=50)
    flags, score = evaluate_ip_risk(info)
    flag = next(f for f in flags if f.code == "IP_HIGH_ABUSE_SCORE")
    assert flag.severity == "high"
    assert score >= 40


def test_tor_dispara_flag_bajo():
    info = AbuseIpInfo(ip_address="1.2.3.4", is_tor=True)
    flags, score = evaluate_ip_risk(info)
    flag = next(f for f in flags if f.code == "IP_TOR_EXIT_NODE")
    assert flag.severity == "low"


def test_combinacion_no_supera_100():
    info = AbuseIpInfo(ip_address="1.2.3.4", abuse_confidence_score=100, total_reports=999, is_tor=True)
    _, score = evaluate_ip_risk(info)
    assert score <= 100
