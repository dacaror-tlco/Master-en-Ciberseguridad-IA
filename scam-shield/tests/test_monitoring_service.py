"""
Tests unitarios del motor de monitorización continua (app/services/monitoring_service.py).
No pasan por la API: llaman directamente a las funciones con una Session real
sobre la base en memoria (fixture `db`, ver conftest.py).
"""
from app.schemas.domain_analysis import RiskFlag
from app.services import monitoring_service


def _flag(code="SOME_FLAG", severity="low"):
    return [RiskFlag(code=code, description="algo", severity=severity)]


def test_risk_bucket_usa_los_mismos_cortes_que_el_frontend():
    assert monitoring_service.risk_bucket(0) == "low"
    assert monitoring_service.risk_bucket(29) == "low"
    assert monitoring_service.risk_bucket(30) == "medium"
    assert monitoring_service.risk_bucket(59) == "medium"
    assert monitoring_service.risk_bucket(60) == "high"
    assert monitoring_service.risk_bucket(100) == "high"


def test_primer_chequeo_de_un_sujeto_no_genera_alerta(db):
    alert = monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=10, flags=_flag())
    assert alert is None

    subject = monitoring_service.get_or_create_subject(db, "domain", "ejemplo.com")
    assert subject.last_case_id == 1
    assert subject.last_score == 10
    assert subject.last_bucket == "low"
    assert subject.enabled is True


def test_subir_de_nivel_genera_alerta(db):
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=10, flags=_flag())
    alert = monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=2, score=65, flags=_flag("DOMAIN_VERY_NEW", "high"))

    assert alert is not None
    assert alert.previous_bucket == "low"
    assert alert.new_bucket == "high"
    assert alert.previous_score == 10
    assert alert.new_score == 65
    assert alert.new_case_id == 2
    assert "DOMAIN_VERY_NEW" in alert.new_flag_codes
    assert alert.acknowledged is False


def test_subida_de_score_dentro_del_mismo_nivel_tambien_genera_alerta_si_supera_el_umbral(db):
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=30, flags=_flag())
    # +20 puntos, sigue en "medium" (30-59) pero supera monitoring_score_change_threshold (15 por defecto)
    alert = monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=2, score=50, flags=_flag())

    assert alert is not None
    assert alert.previous_bucket == "medium"
    assert alert.new_bucket == "medium"


def test_pequena_variacion_sin_cambio_de_nivel_no_genera_alerta(db):
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=10, flags=_flag())
    alert = monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=2, score=15, flags=_flag())
    assert alert is None


def test_bajar_de_nivel_no_genera_alerta(db):
    """Monitorizamos que el riesgo SUBA, no que baje — bajar no es una alerta que requiera acción."""
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=80, flags=_flag())
    alert = monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=2, score=20, flags=_flag())
    assert alert is None

    subject = monitoring_service.get_or_create_subject(db, "domain", "ejemplo.com")
    assert subject.last_score == 20
    assert subject.last_bucket == "low"


def test_sujetos_distintos_no_se_mezclan(db):
    monitoring_service.touch_subject(db, "domain", "uno.com", case_id=1, score=10, flags=_flag())
    monitoring_service.touch_subject(db, "wallet", "uno.com", case_id=2, score=90, flags=_flag())

    subjects = monitoring_service.list_subjects(db)
    assert len(subjects) == 2
    assert {s.case_type for s in subjects} == {"domain", "wallet"}


def test_list_subjects_filtra_por_case_type(db):
    monitoring_service.touch_subject(db, "domain", "uno.com", case_id=1, score=10, flags=_flag())
    monitoring_service.touch_subject(db, "wallet", "dos", case_id=2, score=10, flags=_flag())

    only_domains = monitoring_service.list_subjects(db, case_type="domain")
    assert len(only_domains) == 1
    assert only_domains[0].case_type == "domain"


def test_update_subject_permite_desactivar_y_cambiar_intervalo(db):
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=10, flags=_flag())
    subject = monitoring_service.get_or_create_subject(db, "domain", "ejemplo.com")

    updated = monitoring_service.update_subject(db, subject.id, enabled=False, check_interval_hours=6)
    assert updated.enabled is False
    assert updated.check_interval_hours == 6


def test_update_subject_inexistente_devuelve_none(db):
    assert monitoring_service.update_subject(db, 9999, enabled=False, check_interval_hours=None) is None


def test_list_alerts_y_acknowledge(db):
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=1, score=10, flags=_flag())
    monitoring_service.touch_subject(db, "domain", "ejemplo.com", case_id=2, score=70, flags=_flag())

    alerts = monitoring_service.list_alerts(db)
    assert len(alerts) == 1
    assert alerts[0].acknowledged is False

    unack = monitoring_service.list_alerts(db, unacknowledged_only=True)
    assert len(unack) == 1

    acked = monitoring_service.acknowledge_alert(db, alerts[0].id)
    assert acked.acknowledged is True

    unack_after = monitoring_service.list_alerts(db, unacknowledged_only=True)
    assert len(unack_after) == 0


def test_acknowledge_alert_inexistente_devuelve_none(db):
    assert monitoring_service.acknowledge_alert(db, 9999) is None
