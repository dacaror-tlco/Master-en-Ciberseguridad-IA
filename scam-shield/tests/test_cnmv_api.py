from unittest.mock import MagicMock, patch

_FAKE_PAGE_WITH_ENTRIES = """
<html><body>
<table>
<tr><th>Fecha</th><th>Compañías sobre las que se advierte</th><th>Documento</th><th>Documento (en inglés)</th><th>Observaciones</th></tr>
<tr><td>18/05/2026</td><td>HTTPS://AICHAINTRADER.COM/ES/<br>AI CHAIN TRADER</td><td>x</td><td>x</td><td></td></tr>
</table>
</body></html>
"""
_FAKE_EMPTY_PAGE = "<html><body><table><tr><th>Fecha</th><th>Compañías</th></tr></table></body></html>"


def _fake_get(url, params=None, timeout=None, headers=None):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.text = _FAKE_PAGE_WITH_ENTRIES if params.get("page") == 0 else _FAKE_EMPTY_PAGE
    return resp


def test_busqueda_con_coincidencia(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        response = client.post("/analysis/cnmv-check", json={"query": "aichaintrader"})

    assert response.status_code == 200
    data = response.json()
    assert data["match_count"] == 1
    assert data["risk_score"] == 90
    assert "CNMV_UNAUTHORIZED_ENTITY" in [f["code"] for f in data["risk_flags"]]


def test_busqueda_sin_coincidencia(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        response = client.post("/analysis/cnmv-check", json={"query": "empresa-legitima-que-no-existe"})

    data = response.json()
    assert data["match_count"] == 0
    assert data["risk_score"] == 0
    assert data["risk_flags"] == []


def test_busqueda_no_distingue_mayusculas(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        response = client.post("/analysis/cnmv-check", json={"query": "AiChainTrader"})

    assert response.json()["match_count"] == 1


def test_busqueda_vacia_da_400(client):
    response = client.post("/analysis/cnmv-check", json={"query": "   "})
    assert response.status_code == 400


def test_cache_solo_se_refresca_una_vez_por_ventana(client):
    """La segunda búsqueda no debería volver a llamar a la red si la caché sigue fresca."""
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get) as mock_get:
        client.post("/analysis/cnmv-check", json={"query": "primera"})
        calls_after_first = mock_get.call_count
        client.post("/analysis/cnmv-check", json={"query": "segunda"})
        calls_after_second = mock_get.call_count

    assert calls_after_first > 0
    assert calls_after_second == calls_after_first  # no ha vuelto a llamar a la red


def test_fallo_de_red_no_rompe_la_busqueda(client):
    """Si la CNMV no responde, la búsqueda sigue funcionando (con 0 resultados y el error anotado), no un 500."""
    with patch("app.services.cnmv_service.requests.get", side_effect=Exception("timeout")):
        response = client.post("/analysis/cnmv-check", json={"query": "cualquier cosa"})

    assert response.status_code == 200
    data = response.json()
    assert data["match_count"] == 0
    assert any("CNMV" in e for e in data["errors"])


def test_pagina_con_estructura_inesperada_se_reporta_como_error_no_como_0_resultados_silenciosos(client):
    resp_mock = MagicMock()
    resp_mock.raise_for_status.return_value = None
    resp_mock.text = "<html><body>estructura completamente distinta, sin tabla</body></html>"

    with patch("app.services.cnmv_service.requests.get", return_value=resp_mock):
        response = client.post("/analysis/cnmv-check", json={"query": "cualquier cosa"})

    data = response.json()
    assert any("CNMV" in e for e in data["errors"])


def test_estado_de_cache(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        client.post("/analysis/cnmv-check", json={"query": "aichaintrader"})

    status = client.get("/cnmv-warnings/cache-status").json()
    assert status["cached_warnings"] == 1
    assert status["last_refreshed"] is not None


def test_listado_y_detalle_de_casos(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        created = client.post("/analysis/cnmv-check", json={"query": "aichaintrader"}).json()

    listado = client.get("/cnmv-check-cases")
    assert len(listado.json()) == 1

    detalle = client.get(f"/cnmv-check-cases/{created['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["query"] == "aichaintrader"


def test_caso_inexistente_da_404(client):
    response = client.get("/cnmv-check-cases/9999")
    assert response.status_code == 404


def test_sin_credenciales_fca_degrada_con_gracia(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get):
        response = client.post("/analysis/cnmv-check", json={"query": "empresa-legitima-que-no-existe"})

    data = response.json()
    assert data["fca_matches"] == []
    assert any("FCA Register" in e for e in data["errors"])


def test_fca_match_no_autorizado_dispara_senal(client):
    fca_resp = MagicMock()
    fca_resp.json.return_value = {
        "Data": [{"Name": "Scam Broker Ltd", "Reference Number": "999999", "Status": "No longer authorised", "Type of business or Individual": "Firm"}]
    }
    fca_resp.raise_for_status.return_value = None

    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get), \
         patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=fca_resp):
        response = client.post("/analysis/cnmv-check", json={"query": "empresa-legitima-que-no-existe"})

    data = response.json()
    assert data["fca_matches"][0]["status"] == "No longer authorised"
    assert "FCA_NOT_CURRENTLY_AUTHORISED" in [f["code"] for f in data["risk_flags"]]


def test_fca_clone_scam_dispara_senal_alta(client):
    """Regresión con datos reales: la propia búsqueda de la FCA marca clones/no autorizadas explícitamente."""
    fca_resp = MagicMock()
    fca_resp.json.return_value = {
        "Data": [{
            "Name": "Barclays Capital (clone of FCA authorised firm)", "Reference Number": "",
            "Status": "Unauthorised", "Type of business or Individual": "Unauthorised firm", "URL": None,
        }]
    }
    fca_resp.raise_for_status.return_value = None

    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get), \
         patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=fca_resp):
        response = client.post("/analysis/cnmv-check", json={"query": "Barclays"})

    data = response.json()
    assert data["fca_matches"][0]["type_of_business"] == "Unauthorised firm"
    assert "FCA_UNAUTHORISED_FIRM" in [f["code"] for f in data["risk_flags"]]


def test_no_encontrado_en_registro_cnmv_dispara_senal(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get), \
         patch("app.services.cnmv_registry_service.search_registered_entities", return_value=[]):
        response = client.post("/analysis/cnmv-check", json={"query": "empresa-legitima-que-no-existe"})

    data = response.json()
    assert data["registry_matches"] == []
    assert "CNMV_NOT_IN_AUTHORIZED_REGISTRY" in [f["code"] for f in data["risk_flags"]]


def test_encontrado_en_registro_cnmv_no_dispara_senal(client):
    from app.schemas.cnmv import CnmvRegisteredEntity

    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get), \
         patch(
             "app.services.cnmv_registry_service.search_registered_entities",
             return_value=[CnmvRegisteredEntity(code="A82473018", name="RENTA 4 BANCO, S.A.")],
         ):
        response = client.post("/analysis/cnmv-check", json={"query": "Renta 4"})

    data = response.json()
    assert data["registry_matches"][0]["name"] == "RENTA 4 BANCO, S.A."
    assert "CNMV_NOT_IN_AUTHORIZED_REGISTRY" not in [f["code"] for f in data["risk_flags"]]


def test_fallo_del_registro_cnmv_no_dispara_senal_solo_queda_en_errors(client):
    with patch("app.services.cnmv_service.requests.get", side_effect=_fake_get), \
         patch("app.services.cnmv_registry_service.search_registered_entities", side_effect=Exception("timeout")):
        response = client.post("/analysis/cnmv-check", json={"query": "cualquier cosa"})

    data = response.json()
    assert data["registry_matches"] is None
    assert "CNMV_NOT_IN_AUTHORIZED_REGISTRY" not in [f["code"] for f in data["risk_flags"]]
    assert any("Registro de entidades CNMV" in e for e in data["errors"])
