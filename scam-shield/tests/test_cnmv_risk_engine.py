from app.schemas.cnmv import CnmvMatch, CnmvRegisteredEntity, FcaMatch
from app.services.cnmv_risk_engine import evaluate_cnmv_risk


def test_sin_coincidencias_da_score_cero():
    flags, score = evaluate_cnmv_risk([])
    assert flags == []
    assert score == 0


def test_una_coincidencia_dispara_flag_alto():
    match = CnmvMatch(fecha="18/05/2026", companias="AI CHAIN TRADER")
    flags, score = evaluate_cnmv_risk([match])
    assert len(flags) == 1
    assert flags[0].code == "CNMV_UNAUTHORIZED_ENTITY"
    assert flags[0].severity == "high"
    assert score == 90


def test_varias_coincidencias_siguen_dando_el_mismo_score_alto():
    matches = [
        CnmvMatch(fecha="18/05/2026", companias="A"),
        CnmvMatch(fecha="11/05/2026", companias="B"),
    ]
    flags, score = evaluate_cnmv_risk(matches)
    assert score == 90
    assert "2" in flags[0].description


def test_sin_fca_matches_no_anade_senal():
    flags, score = evaluate_cnmv_risk([], [])
    assert flags == []
    assert score == 0


def test_fca_match_autorizado_no_dispara_senal():
    fca_matches = [FcaMatch(name="Barclays Bank Plc", reference_number="122702", status="Authorised")]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    assert flags == []
    assert score == 0


def test_fca_match_no_autorizado_dispara_flag_medio():
    fca_matches = [FcaMatch(name="Scam Broker Ltd", reference_number="999999", status="No longer authorised")]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    flag = next(f for f in flags if f.code == "FCA_NOT_CURRENTLY_AUTHORISED")
    assert flag.severity == "medium"
    assert score == 30


def test_fca_registered_tambien_cuenta_como_activo():
    fca_matches = [FcaMatch(name="Some Fund", reference_number="1", status="Registered")]
    flags, _ = evaluate_cnmv_risk([], fca_matches)
    assert flags == []


def test_cnmv_y_fca_se_combinan_sin_superar_100():
    cnmv_matches = [CnmvMatch(fecha="18/05/2026", companias="AI CHAIN TRADER")]
    fca_matches = [FcaMatch(name="AI Chain Trader", reference_number="1", status="Cancelled")]
    flags, score = evaluate_cnmv_risk(cnmv_matches, fca_matches)
    codes = {f.code for f in flags}
    assert {"CNMV_UNAUTHORIZED_ENTITY", "FCA_NOT_CURRENTLY_AUTHORISED"} <= codes
    assert score == 100


def test_banco_grande_con_historial_mixto_no_dispara_lapsed():
    """
    Regresión con datos reales (buscando 'Santander'): un grupo con
    décadas de historial en el Reino Unido acumula entidades antiguas
    "No longer authorised" (fusiones, marcas absorbidas) de forma
    totalmente normal — si TAMBIÉN hay coincidencias con autorización
    activa, esa mezcla no debe disparar FCA_NOT_CURRENTLY_AUTHORISED.
    """
    fca_matches = [
        FcaMatch(name="Santander UK Plc", reference_number="106054", status="Authorised"),
        FcaMatch(name="Banco Santander, S.A.", reference_number="136261", status="Authorised"),
        FcaMatch(name="Abbey Stockbrokers Limited", reference_number="154210", status="No longer authorised"),
        FcaMatch(name="Alliance & Leicester Plc", reference_number="189099", status="No longer authorised"),
    ]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    assert "FCA_NOT_CURRENTLY_AUTHORISED" not in [f.code for f in flags]
    assert score == 0


def test_clon_junto_a_entidad_activa_aclara_que_no_es_sobre_la_buscada():
    """Mismo caso Santander: además del historial mixto, hay un clon real detectado."""
    fca_matches = [
        FcaMatch(name="Santander UK Plc", reference_number="106054", status="Authorised"),
        FcaMatch(
            name="Santander Bank Finance/ www.santanderbank-finances.com (Clone of FCA Authorised firm)",
            reference_number="", status="Unauthorised", type_of_business="Unauthorised firm",
        ),
    ]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    flag = next(f for f in flags if f.code == "FCA_UNAUTHORISED_FIRM")
    assert "NO es sobre la entidad buscada" in flag.description
    assert "FCA_NOT_CURRENTLY_AUTHORISED" not in [f.code for f in flags]
    assert score == 60


def test_todo_lapsed_sin_ninguna_activa_si_dispara_la_senal():
    fca_matches = [FcaMatch(name="Old Firm Ltd", reference_number="1", status="No longer authorised")]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    assert "FCA_NOT_CURRENTLY_AUTHORISED" in [f.code for f in flags]
    assert score == 30


def test_fca_unauthorised_firm_dispara_flag_alto():
    fca_matches = [FcaMatch(
        name="Barclays Capital (clone of FCA authorised firm)", reference_number="",
        status="Unauthorised", type_of_business="Unauthorised firm",
    )]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    flag = next(f for f in flags if f.code == "FCA_UNAUTHORISED_FIRM")
    assert flag.severity == "high"
    assert score == 60
    # No debe duplicarse también como FCA_NOT_CURRENTLY_AUTHORISED (misma coincidencia).
    assert "FCA_NOT_CURRENTLY_AUTHORISED" not in [f.code for f in flags]


def test_fca_unauthorised_firm_y_lapsed_por_separado():
    fca_matches = [
        FcaMatch(name="Clone Ltd", reference_number="", status="Unauthorised", type_of_business="Unauthorised firm"),
        FcaMatch(name="Old Firm Ltd", reference_number="1", status="No longer authorised", type_of_business="Firm"),
    ]
    flags, score = evaluate_cnmv_risk([], fca_matches)
    codes = {f.code for f in flags}
    assert {"FCA_UNAUTHORISED_FIRM", "FCA_NOT_CURRENTLY_AUTHORISED"} <= codes
    assert score == 90


def test_registry_matches_none_no_dispara_nada():
    """Si la comprobación no se llegó a hacer (o falló), no hay base para decir 'no encontrado'."""
    flags, score = evaluate_cnmv_risk([], [], None)
    assert flags == []
    assert score == 0


def test_registry_matches_vacia_dispara_flag_medio():
    """Se comprobó de verdad y no se encontró ninguna entidad — sí hay base para la señal."""
    flags, score = evaluate_cnmv_risk([], [], [])
    flag = next(f for f in flags if f.code == "CNMV_NOT_IN_AUTHORIZED_REGISTRY")
    assert flag.severity == "medium"
    assert score == 25


def test_registry_matches_con_resultados_no_dispara_nada():
    registry_matches = [CnmvRegisteredEntity(code="A82473018", name="RENTA 4 BANCO, S.A.")]
    flags, score = evaluate_cnmv_risk([], [], registry_matches)
    assert flags == []
    assert score == 0


def test_todas_las_senales_cnmv_se_combinan_sin_superar_100():
    cnmv_matches = [CnmvMatch(fecha="18/05/2026", companias="AI CHAIN TRADER")]
    fca_matches = [FcaMatch(name="Clone Ltd", reference_number="", status="Unauthorised", type_of_business="Unauthorised firm")]
    flags, score = evaluate_cnmv_risk(cnmv_matches, fca_matches, [])
    codes = {f.code for f in flags}
    assert {"CNMV_UNAUTHORIZED_ENTITY", "FCA_UNAUTHORISED_FIRM", "CNMV_NOT_IN_AUTHORIZED_REGISTRY"} <= codes
    assert score == 100
