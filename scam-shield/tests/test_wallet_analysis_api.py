from unittest.mock import MagicMock, patch

ETH_ADDR = "0x" + "a" * 40
TRON_ADDR = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


def _btc_response(n_tx=3, total_received=100000000, total_sent=0, final_balance=100000000, txs=None):
    resp = MagicMock()
    resp.json.return_value = {
        "n_tx": n_tx, "total_received": total_received, "total_sent": total_sent,
        "final_balance": final_balance, "txs": txs or [],
    }
    resp.raise_for_status.return_value = None
    return resp


def _json_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def _evm_multi_chain_get(balances: dict, txs_by_chain: dict):
    """
    side_effect para `requests.get` que simula Etherscan V2, distinguiendo
    la red por el `chainid` que llega en los params (igual que hace la app).
    """
    def _get(url, params=None, timeout=None, headers=None):
        chain_id = params["chainid"]
        if params["action"] == "balance":
            return _json_response({"result": str(balances.get(chain_id, 0))})
        return _json_response({"result": txs_by_chain.get(chain_id, [])})
    return _get


def _evm_tx(value_wei, timestamp, to_addr, from_addr):
    return {"value": str(value_wei), "timeStamp": str(timestamp), "to": to_addr, "from": from_addr}


def test_analizar_wallet_btc(client):
    with patch("app.services.wallet_service.requests.get", return_value=_btc_response()):
        response = client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})

    assert response.status_code == 200
    data = response.json()
    assert data["wallet"]["chain"] == "BTC"
    assert data["wallet"]["balance"] == 1.0


def test_wallet_sospechosa_dispara_senales(client):
    fake_txs = [{"time": 1751000000 + i * 1000, "inputs": [{"prev_out": {"addr": f"1Sender{i}"}}]} for i in range(12)]
    resp = _btc_response(n_tx=12, total_received=500000000, total_sent=480000000, final_balance=20000000, txs=fake_txs)
    with patch("app.services.wallet_service.requests.get", return_value=resp):
        response = client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})

    codes = [f["code"] for f in response.json()["risk_flags"]]
    assert "HIGH_FAN_IN" in codes
    assert "RAPID_OUTFLOW" in codes


def test_direccion_con_formato_invalido_da_400(client):
    response = client.post("/analysis/wallet", json={"address": "esto-no-es-una-wallet"})
    assert response.status_code == 400


def test_eth_sin_api_key_da_502(client):
    with patch("app.core.config.settings.etherscan_api_key", ""):
        response = client.post("/analysis/wallet", json={"address": "0x" + "a" * 40})
    assert response.status_code == 502


def test_listado_de_casos_de_wallet(client):
    with patch("app.services.wallet_service.requests.get", return_value=_btc_response()):
        client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})

    response = client.get("/wallet-cases")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_eth_usa_la_red_evm_con_mas_actividad(client):
    """Regresión: una wallet sin historial en Ethereum pero muy activa en BSC
    (gas barato, típico de scams) no debe reportarse como WALLET_NO_HISTORY."""
    txs_bsc = [_evm_tx(10**18, 1751000000 + i, ETH_ADDR, f"0x{'b'*39}{i}") for i in range(6)]
    get_mock = _evm_multi_chain_get(
        balances={1: 0, 56: 5 * 10**18, 137: 0},
        txs_by_chain={1: [], 56: txs_bsc, 137: []},
    )
    with patch("app.core.config.settings.etherscan_api_key", "fake-key"), \
         patch("app.services.wallet_service.requests.get", side_effect=get_mock):
        response = client.post("/analysis/wallet", json={"address": ETH_ADDR})

    assert response.status_code == 200
    data = response.json()["wallet"]
    assert data["evm_network"] == "BSC"
    assert data["n_transactions"] == 6
    assert "no tiene actividad" not in (data["note"] or "") or "BSC" in data["note"]
    codes = [f["code"] for f in response.json()["risk_flags"]]
    assert "WALLET_NO_HISTORY" not in codes


def test_eth_sin_actividad_en_ninguna_red_da_no_history(client):
    get_mock = _evm_multi_chain_get(balances={1: 0, 56: 0, 137: 0}, txs_by_chain={1: [], 56: [], 137: []})
    with patch("app.core.config.settings.etherscan_api_key", "fake-key"), \
         patch("app.services.wallet_service.requests.get", side_effect=get_mock):
        response = client.post("/analysis/wallet", json={"address": ETH_ADDR})

    assert response.status_code == 200
    codes = [f["code"] for f in response.json()["risk_flags"]]
    assert "WALLET_NO_HISTORY" in codes


def test_tron_con_movimientos_usdt_usa_esa_senal(client):
    transfers = [
        {"value": str(500 * 10**6), "to": TRON_ADDR, "from": f"TSender{i}xxxxxxxxxxxxxxxxxxxxxxxxxx"[:34], "block_timestamp": 1751000000000 + i * 1000}
        for i in range(3)
    ]

    def _get(url, params=None, headers=None, timeout=None):
        if url.endswith(f"/v1/accounts/{TRON_ADDR}"):
            return _json_response({"data": [{"balance": 10_000_000}]})
        if url.endswith("/transactions/trc20"):
            return _json_response({"data": transfers})
        raise AssertionError(f"URL Tron inesperada: {url}")

    with patch("app.services.wallet_service.requests.get", side_effect=_get):
        response = client.post("/analysis/wallet", json={"address": TRON_ADDR})

    assert response.status_code == 200
    data = response.json()["wallet"]
    assert data["chain"] == "TRON"
    assert data["token"] == "USDT-TRC20"
    assert data["n_transactions"] == 3
    assert data["balance"] == 10.0
    assert data["total_received"] == 1500.0


def test_tron_sin_usdt_cae_a_trx_nativo(client):
    def _get(url, params=None, headers=None, timeout=None):
        if url.endswith(f"/v1/accounts/{TRON_ADDR}"):
            return _json_response({"data": [{"balance": 10_000_000}]})
        if url.endswith("/transactions/trc20"):
            return _json_response({"data": []})
        if url.endswith("/transactions"):
            return _json_response({"data": [{"block_timestamp": 1751000000000}]})
        raise AssertionError(f"URL Tron inesperada: {url}")

    with patch("app.services.wallet_service.requests.get", side_effect=_get):
        response = client.post("/analysis/wallet", json={"address": TRON_ADDR})

    assert response.status_code == 200
    data = response.json()["wallet"]
    assert data["chain"] == "TRON"
    assert data["token"] is None
    assert data["n_transactions"] == 1
    assert "TRX" in data["note"]


def test_direccion_sancionada_por_ofac_marca_wallet(client):
    with patch("app.services.wallet_service.requests.get", return_value=_btc_response()), \
         patch("app.services.ofac_service.is_sanctioned", return_value=True):
        response = client.post("/analysis/wallet", json={"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})

    data = response.json()
    assert data["wallet"]["ofac_sanctioned"] is True
    assert data["risk_score"] == 100
    assert "WALLET_OFAC_SANCTIONED" in [f["code"] for f in data["risk_flags"]]


def test_extraer_direcciones_de_texto_libre(client):
    text = f"Envía el pago a {TRON_ADDR} o a 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa, gracias"
    response = client.post("/analysis/wallet/extract-addresses", json={"text": text})

    assert response.status_code == 200
    candidates = {(c["address"], c["chain"]) for c in response.json()["candidates"]}
    assert candidates == {(TRON_ADDR, "TRON"), ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC")}


def test_extraer_direcciones_sin_ninguna_da_lista_vacia(client):
    response = client.post("/analysis/wallet/extract-addresses", json={"text": "no hay nada aquí"})
    assert response.json()["candidates"] == []


def test_formato_de_direccion_detecta_chain_y_subtipo(client):
    response = client.get("/analysis/wallet/format", params={"address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"})
    assert response.status_code == 200
    assert response.json() == {"chain": "BTC", "subtype": "bech32 (SegWit nativo)", "valid": True}


def test_formato_de_direccion_no_reconocido(client):
    response = client.get("/analysis/wallet/format", params={"address": "no-es-una-wallet"})
    assert response.json() == {"chain": None, "subtype": None, "valid": False}
