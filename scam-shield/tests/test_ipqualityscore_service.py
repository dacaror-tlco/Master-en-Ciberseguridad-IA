from unittest.mock import MagicMock, patch

import pytest

from app.services import ipqualityscore_service


def test_sin_api_key_lanza_runtimeerror():
    with patch("app.core.config.settings.ipqualityscore_api_key", ""):
        with pytest.raises(RuntimeError, match="IPQUALITYSCORE_API_KEY"):
            ipqualityscore_service.get_fraud_score("+34600123456")


def test_success_false_lanza_runtimeerror():
    resp = MagicMock()
    resp.json.return_value = {"success": False, "message": "Número no válido"}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.ipqualityscore_api_key", "fake-key"), \
         patch("app.services.ipqualityscore_service.requests.get", return_value=resp):
        with pytest.raises(RuntimeError, match="Número no válido"):
            ipqualityscore_service.get_fraud_score("+34600123456")


def test_parsea_senales_de_comportamiento():
    resp = MagicMock()
    resp.json.return_value = {
        "success": True, "fraud_score": 92, "VOIP": True, "prepaid": True,
        "recent_abuse": True, "leaked": False, "spammer": True, "active": True,
        "line_type": "Voip", "carrier": "Some Carrier",
        "name": "Juan Pérez",  # identidad — no debe acabar en ningún campo del schema
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.ipqualityscore_api_key", "fake-key"), \
         patch("app.services.ipqualityscore_service.requests.get", return_value=resp):
        info = ipqualityscore_service.get_fraud_score("+34600123456")

    assert info.fraud_score == 92
    assert info.voip is True
    assert info.prepaid is True
    assert info.recent_abuse is True
    assert info.leaked is False
    assert info.spammer is True
    # Regresión: el campo `name` (identidad) de la API real NUNCA debe leerse ni exponerse.
    assert not hasattr(info, "name")
    assert "Juan Pérez" not in info.model_dump_json()


def test_numero_se_envia_sin_el_signo_mas():
    resp = MagicMock()
    resp.json.return_value = {"success": True, "fraud_score": 0}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.ipqualityscore_api_key", "fake-key"), \
         patch("app.services.ipqualityscore_service.requests.get", return_value=resp) as mock_get:
        ipqualityscore_service.get_fraud_score("+34600123456")

    called_url = mock_get.call_args[0][0]
    assert "+34600123456" not in called_url
    assert "34600123456" in called_url
