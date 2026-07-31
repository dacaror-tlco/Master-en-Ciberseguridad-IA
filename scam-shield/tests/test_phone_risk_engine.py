from app.schemas.phone_analysis import CarrierIntelligenceInfo, CommunityReportInfo, FraudScoreInfo, PhoneInfo
from app.services.phone_risk_engine import evaluate_phone_risk


def _phone(**overrides) -> PhoneInfo:
    base = dict(
        e164="+34600123456", international_format="+34 600 12 34 56", national_format="600 12 34 56",
        country_code=34, country_name="ES", line_type="MOBILE", is_valid=True, is_possible=True,
    )
    base.update(overrides)
    return PhoneInfo(**base)


def test_movil_normal_da_score_cero():
    flags, score = evaluate_phone_risk(_phone())
    assert score == 0
    assert flags == []


def test_tarificacion_especial_dispara_flag_alto():
    flags, score = evaluate_phone_risk(_phone(line_type="PREMIUM_RATE"))
    assert "PHONE_PREMIUM_RATE" in [f.code for f in flags]
    assert score >= 50


def test_voip_dispara_flag_medio():
    flags, score = evaluate_phone_risk(_phone(line_type="VOIP"))
    flag = next(f for f in flags if f.code == "PHONE_VOIP")
    assert flag.severity == "medium"
    assert score >= 20


def test_formato_invalido_dispara_flag():
    flags, score = evaluate_phone_risk(_phone(is_valid=False))
    assert "PHONE_INVALID_FORMAT" in [f.code for f in flags]


def test_toll_free_no_dispara_nada():
    flags, score = evaluate_phone_risk(_phone(line_type="TOLL_FREE"))
    assert flags == []
    assert score == 0


def test_fixed_line_no_dispara_nada():
    flags, score = evaluate_phone_risk(_phone(line_type="FIXED_LINE"))
    assert flags == []
    assert score == 0


def test_pager_dispara_flag_bajo():
    flags, score = evaluate_phone_risk(_phone(line_type="PAGER"))
    flag = next(f for f in flags if f.code == "PHONE_PAGER")
    assert flag.severity == "low"
    assert score == 5


def test_unknown_valido_dispara_flag_bajo():
    flags, _ = evaluate_phone_risk(_phone(line_type="UNKNOWN", is_valid=True))
    flag = next(f for f in flags if f.code == "PHONE_UNKNOWN_LINE_TYPE")
    assert flag.severity == "low"


def test_caso_combinado_no_supera_100():
    flags, score = evaluate_phone_risk(_phone(line_type="PREMIUM_RATE", is_valid=False))
    codes = {f.code for f in flags}
    assert {"PHONE_PREMIUM_RATE", "PHONE_INVALID_FORMAT"} <= codes
    assert score <= 100


def test_sin_reportes_comunitarios_no_anade_senal():
    flags, score = evaluate_phone_risk(_phone(), CommunityReportInfo(reports_count=0))
    assert flags == []
    assert score == 0


def test_muchos_reportes_nivel_alto_dispara_flag_alto():
    community = CommunityReportInfo(reports_count=47, category="fraude", danger_level="alto")
    flags, score = evaluate_phone_risk(_phone(), community)
    flag = next(f for f in flags if f.code == "PHONE_COMMUNITY_REPORTED_HIGH")
    assert flag.severity == "high"
    assert score >= 45


def test_reportes_moderados_dispara_flag_medio():
    community = CommunityReportInfo(reports_count=8, category="telemarketing", danger_level="medio")
    flags, score = evaluate_phone_risk(_phone(), community)
    flag = next(f for f in flags if f.code == "PHONE_COMMUNITY_REPORTED_MEDIUM")
    assert flag.severity == "medium"


def test_pocos_reportes_sin_nivel_dispara_flag_bajo():
    community = CommunityReportInfo(reports_count=1, category="publicidad")
    flags, _ = evaluate_phone_risk(_phone(), community)
    flag = next(f for f in flags if f.code == "PHONE_COMMUNITY_REPORTED_LOW")
    assert flag.severity == "low"


def test_conteo_alto_dispara_high_aunque_no_venga_nivel_peligro():
    """Si la API no manda 'nivel_peligro' pero el conteo es muy alto, igualmente se marca como alto."""
    community = CommunityReportInfo(reports_count=25, category="fraude", danger_level=None)
    flags, _ = evaluate_phone_risk(_phone(), community)
    assert "PHONE_COMMUNITY_REPORTED_HIGH" in [f.code for f in flags]


def test_reportes_y_premium_rate_se_combinan():
    community = CommunityReportInfo(reports_count=47, category="fraude", danger_level="alto")
    flags, score = evaluate_phone_risk(_phone(line_type="PREMIUM_RATE"), community)
    codes = {f.code for f in flags}
    assert {"PHONE_PREMIUM_RATE", "PHONE_COMMUNITY_REPORTED_HIGH"} <= codes
    assert score == 95


def test_sin_fraud_info_no_anade_senal():
    flags, score = evaluate_phone_risk(_phone(), fraud_info=None)
    assert flags == []
    assert score == 0


def test_fraud_score_alto_dispara_flag_alto():
    fraud = FraudScoreInfo(fraud_score=90)
    flags, score = evaluate_phone_risk(_phone(), fraud_info=fraud)
    flag = next(f for f in flags if f.code == "PHONE_HIGH_FRAUD_SCORE")
    assert flag.severity == "high"
    assert score >= 40


def test_fraud_score_moderado_dispara_flag_medio():
    fraud = FraudScoreInfo(fraud_score=70)
    flags, score = evaluate_phone_risk(_phone(), fraud_info=fraud)
    flag = next(f for f in flags if f.code == "PHONE_MODERATE_FRAUD_SCORE")
    assert flag.severity == "medium"


def test_fraud_score_bajo_no_dispara_nada():
    fraud = FraudScoreInfo(fraud_score=10)
    flags, score = evaluate_phone_risk(_phone(), fraud_info=fraud)
    assert flags == []
    assert score == 0


def test_abuso_reciente_dispara_flag_alto():
    fraud = FraudScoreInfo(recent_abuse=True)
    flags, score = evaluate_phone_risk(_phone(), fraud_info=fraud)
    flag = next(f for f in flags if f.code == "PHONE_RECENT_ABUSE_REPORTED")
    assert flag.severity == "high"


def test_numero_filtrado_dispara_flag_bajo():
    fraud = FraudScoreInfo(leaked=True)
    flags, score = evaluate_phone_risk(_phone(), fraud_info=fraud)
    flag = next(f for f in flags if f.code == "PHONE_NUMBER_LEAKED")
    assert flag.severity == "low"


def test_sin_carrier_intel_no_anade_senal():
    flags, score = evaluate_phone_risk(_phone(), carrier_intel=None)
    assert flags == []
    assert score == 0


def test_voip_en_tiempo_real_distinto_al_offline_dispara_flag_alto():
    carrier_intel = CarrierIntelligenceInfo(carrier_name="Some Carrier", line_type="voip")
    flags, score = evaluate_phone_risk(_phone(line_type="MOBILE"), carrier_intel=carrier_intel)
    flag = next(f for f in flags if f.code == "PHONE_VOIP_LIVE_MISMATCH")
    assert flag.severity == "high"
    assert score >= 30


def test_voip_en_tiempo_real_coincide_con_offline_no_duplica_senal():
    carrier_intel = CarrierIntelligenceInfo(carrier_name="Some Carrier", line_type="voip")
    flags, _ = evaluate_phone_risk(_phone(line_type="VOIP"), carrier_intel=carrier_intel)
    assert "PHONE_VOIP_LIVE_MISMATCH" not in [f.code for f in flags]


def test_todas_las_senales_combinadas_no_superan_100():
    community = CommunityReportInfo(reports_count=47, category="fraude", danger_level="alto")
    fraud = FraudScoreInfo(fraud_score=95, recent_abuse=True, leaked=True)
    carrier_intel = CarrierIntelligenceInfo(line_type="voip")
    flags, score = evaluate_phone_risk(_phone(line_type="PREMIUM_RATE"), community, fraud, carrier_intel)
    assert score <= 100
