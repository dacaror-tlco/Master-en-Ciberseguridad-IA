from unittest.mock import MagicMock, patch


def test_ip_invalida_da_400(client):
    response = client.post("/analysis/ip", json={"ip": "esto no es una ip"})
    assert response.status_code == 400


def test_sin_abuseipdb_key_degrada_con_gracia(client):
    response = client.post("/analysis/ip", json={"ip": "1.2.3.4"})
    assert response.status_code == 200
    data = response.json()
    assert data["abuseipdb"] is None
    assert any("AbuseIPDB" in e for e in data["errors"])
    assert data["risk_score"] == 0


def test_ip_con_reputacion_mala_dispara_senal(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "ipAddress": "1.2.3.4", "abuseConfidenceScore": 95, "totalReports": 120,
            "isTor": False, "usageType": "Data Center/Web Hosting/Transit", "isp": "Bad Host", "countryCode": "RU",
        }
    }
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/ip", json={"ip": "1.2.3.4"})

    data = response.json()
    assert data["abuseipdb"]["abuse_confidence_score"] == 95
    assert "IP_HIGH_ABUSE_SCORE" in [f["code"] for f in data["risk_flags"]]
    assert data["risk_score"] >= 40


def test_se_persiste_y_aparece_en_el_listado(client):
    client.post("/analysis/ip", json={"ip": "1.2.3.4"})
    client.post("/analysis/ip", json={"ip": "8.8.8.8"})

    response = client.get("/ip-cases")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_obtener_caso_inexistente_da_404(client):
    response = client.get("/ip-cases/9999")
    assert response.status_code == 404


def test_obtener_caso_concreto(client):
    created = client.post("/analysis/ip", json={"ip": "1.2.3.4"}).json()
    response = client.get(f"/ip-cases/{created['id']}")
    assert response.status_code == 200
    assert response.json()["ip"] == "1.2.3.4"
