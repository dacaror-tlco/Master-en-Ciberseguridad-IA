"""
Tests de integración de la monitorización continua: endpoints
/monitoring/* y /alerts/*, más el runner que usa el scheduler
(app/services/monitoring_runner.py), con las fuentes externas mockeadas
igual que en el resto de la suite.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models.monitoring import MonitoredSubject
from app.services import monitoring_runner


def test_analizar_un_dominio_lo_registra_para_monitorizacion(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    response = client.get("/monitoring/subjects")
    assert response.status_code == 200
    subjects = response.json()
    assert len(subjects) == 1
    assert subjects[0]["case_type"] == "domain"
    assert subjects[0]["identifier"] == "ejemplo.com"
    assert subjects[0]["enabled"] is True
    assert subjects[0]["last_score"] == 0
    assert subjects[0]["last_bucket"] == "low"


def test_reanalizar_el_mismo_dominio_con_mas_riesgo_genera_alerta(client, old_whois, old_ssl, fresh_whois, fresh_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    response = client.get("/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["case_type"] == "domain"
    assert alert["identifier"] == "ejemplo.com"
    assert alert["previous_bucket"] == "low"
    assert alert["new_bucket"] == "high"
    assert alert["acknowledged"] is False


def test_alertas_se_pueden_marcar_como_leidas(client, old_whois, old_ssl, fresh_whois, fresh_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})
    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    alert_id = client.get("/alerts").json()[0]["id"]

    response = client.post(f"/alerts/{alert_id}/acknowledge")
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True

    assert client.get("/alerts?unacknowledged_only=true").json() == []


def test_acknowledge_de_alerta_inexistente_da_404(client):
    response = client.post("/alerts/9999/acknowledge")
    assert response.status_code == 404


def test_patch_subject_permite_desactivar_y_cambiar_intervalo(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    subject_id = client.get("/monitoring/subjects").json()[0]["id"]

    response = client.patch(f"/monitoring/subjects/{subject_id}", json={"enabled": False, "check_interval_hours": 6})
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["check_interval_hours"] == 6


def test_patch_subject_inexistente_da_404(client):
    response = client.patch("/monitoring/subjects/9999", json={"enabled": False})
    assert response.status_code == 404


def test_check_now_reanaliza_y_devuelve_la_alerta_si_la_hay(client, old_whois, old_ssl, fresh_whois, fresh_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    subject_id = client.get("/monitoring/subjects").json()[0]["id"]

    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        response = client.post(f"/monitoring/subjects/{subject_id}/check-now")

    assert response.status_code == 200
    data = response.json()
    assert data["error"] is None
    assert data["alert"] is not None
    assert data["alert"]["new_bucket"] == "high"
    assert data["subject"]["last_score"] > 0

    # Se ha creado un caso nuevo de verdad (no se ha tocado el original) -> ahora hay 2.
    assert len(client.get("/cases").json()) == 2


def test_check_now_de_sujeto_inexistente_da_404(client):
    response = client.post("/monitoring/subjects/9999/check-now")
    assert response.status_code == 404


def test_check_now_propaga_el_error_sin_reventar(client):
    # El análisis de dominio absorbe los fallos de WHOIS/SSL como `errors` internos
    # (nunca lanza), así que para probar la propagación de un fallo real en
    # check-now usamos wallet: ahí un fallo de red SÍ se deja subir tal cual
    # (ver wallet_analysis_service.py).
    btc_response = MagicMock()
    btc_response.json.return_value = {"n_tx": 1, "total_received": 100000000, "total_sent": 0, "final_balance": 100000000, "txs": []}
    btc_response.raise_for_status.return_value = None

    with patch("app.services.wallet_service.requests.get", return_value=btc_response):
        client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})

    subject_id = client.get("/monitoring/subjects").json()[0]["id"]

    with patch("app.services.wallet_service.requests.get", side_effect=Exception("boom")):
        response = client.post(f"/monitoring/subjects/{subject_id}/check-now")

    assert response.status_code == 200
    data = response.json()
    assert data["alert"] is None
    assert "boom" in data["error"]


def test_run_due_checks_solo_re_chequea_lo_que_toca(db, old_whois, old_ssl, fresh_whois, fresh_ssl):
    from app.services.domain_analysis_service import run_domain_analysis

    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        run_domain_analysis(db, "reciente.com")
        run_domain_analysis(db, "atrasado.com")

    subjects = {s.identifier: s for s in db.query(MonitoredSubject).all()}
    # "atrasado.com" lleva más de 24h (su intervalo por defecto) sin chequearse -> le toca.
    subjects["atrasado.com"].last_checked_at = datetime.now(timezone.utc) - timedelta(hours=48)
    db.commit()

    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        result = monitoring_runner.run_due_checks(db)

    assert result["checked"] == 1
    assert result["errors"] == []

    refreshed = {s.identifier: s for s in db.query(MonitoredSubject).all()}
    assert refreshed["atrasado.com"].last_score > 0  # se re-chequeó y subió de riesgo
    assert refreshed["reciente.com"].last_score == 0  # no le tocaba, no se ha tocado


def test_run_due_checks_no_toca_sujetos_desactivados(db, old_whois, old_ssl):
    from app.services.domain_analysis_service import run_domain_analysis

    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        run_domain_analysis(db, "ejemplo.com")

    subject = db.query(MonitoredSubject).filter(MonitoredSubject.identifier == "ejemplo.com").first()
    subject.enabled = False
    subject.last_checked_at = datetime.now(timezone.utc) - timedelta(hours=48)
    db.commit()

    result = monitoring_runner.run_due_checks(db)
    assert result["checked"] == 0
