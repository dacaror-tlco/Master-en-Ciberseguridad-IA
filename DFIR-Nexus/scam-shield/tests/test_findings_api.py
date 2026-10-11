"""
Tests de la API de lectura `/osint-findings` y de que cada análisis
proyecta su finding automáticamente (integración a través de `client`).
"""


def test_analizar_una_ip_crea_su_finding(client):
    client.post("/analysis/ip", json={"ip": "1.2.3.4"})

    findings = client.get("/osint-findings").json()
    assert len(findings) == 1
    f = findings[0]
    assert f["case_type"] == "ip"
    assert f["subject_type"] == "ip_address"
    assert f["subject_value"] == "1.2.3.4"
    assert f["source_table"] == "ip_cases"
    assert f["case_id"] is None
    assert "risk_level" in f and "headline" in f


def test_findings_de_varios_modulos_conviven_y_se_filtran(client):
    from unittest.mock import MagicMock, patch

    btc_resp = MagicMock()
    btc_resp.json.return_value = {"n_tx": 3, "total_received": 100000000, "total_sent": 0, "final_balance": 100000000, "txs": []}
    btc_resp.raise_for_status.return_value = None

    client.post("/analysis/ip", json={"ip": "1.2.3.4"})
    with patch("app.modules.osint.wallet.wallet_service.requests.get", return_value=btc_resp):
        r = client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})
    assert r.status_code == 200

    todos = client.get("/osint-findings").json()
    assert {f["case_type"] for f in todos} == {"ip", "wallet"}

    solo_ip = client.get("/osint-findings", params={"case_type": "ip"}).json()
    assert len(solo_ip) == 1 and solo_ip[0]["case_type"] == "ip"

    solo_wallet = client.get("/osint-findings", params={"subject_type": "crypto_wallet"}).json()
    assert len(solo_wallet) == 1 and solo_wallet[0]["case_type"] == "wallet"
    assert solo_wallet[0]["subject_value"] == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"


def test_detalle_de_un_finding_incluye_payload_y_flags(client):
    client.post("/analysis/ip", json={"ip": "8.8.8.8"})
    finding_id = client.get("/osint-findings").json()[0]["id"]

    detail = client.get(f"/osint-findings/{finding_id}").json()
    assert "details" in detail and "top_flags" in detail
    assert detail["details"]["ip"] == "8.8.8.8"


def test_detalle_inexistente_da_404(client):
    assert client.get("/osint-findings/99999").status_code == 404


def test_un_analisis_que_falla_no_deja_finding_a_medias(client):
    # IP inválida -> 400, no se crea caso ni finding
    assert client.post("/analysis/ip", json={"ip": "no-es-ip"}).status_code == 400
    assert client.get("/osint-findings").json() == []


def test_filtro_por_nivel_de_riesgo(client):
    client.post("/analysis/ip", json={"ip": "1.2.3.4"})  # sin keys -> score 0 -> low
    assert client.get("/osint-findings", params={"risk_level": "low"}).json()
    assert client.get("/osint-findings", params={"risk_level": "high"}).json() == []
