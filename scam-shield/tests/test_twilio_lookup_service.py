from unittest.mock import MagicMock, patch

import pytest

from app.services import twilio_lookup_service


def test_sin_credenciales_lanza_runtimeerror():
    with patch("app.core.config.settings.twilio_account_sid", ""), \
         patch("app.core.config.settings.twilio_auth_token", ""):
        with pytest.raises(RuntimeError, match="TWILIO_ACCOUNT_SID"):
            twilio_lookup_service.get_carrier_intelligence("+34600123456")


def test_solo_falta_auth_token_tambien_lanza_runtimeerror():
    with patch("app.core.config.settings.twilio_account_sid", "AC123"), \
         patch("app.core.config.settings.twilio_auth_token", ""):
        with pytest.raises(RuntimeError, match="TWILIO_ACCOUNT_SID"):
            twilio_lookup_service.get_carrier_intelligence("+34600123456")


def test_parsea_line_type_intelligence():
    resp = MagicMock()
    resp.json.return_value = {
        "line_type_intelligence": {
            "carrier_name": "Vodafone ES", "type": "voip",
            "mobile_country_code": "214", "mobile_network_code": "01",
        }
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.twilio_account_sid", "AC123"), \
         patch("app.core.config.settings.twilio_auth_token", "secret"), \
         patch("app.services.twilio_lookup_service.requests.get", return_value=resp):
        info = twilio_lookup_service.get_carrier_intelligence("+34600123456")

    assert info.carrier_name == "Vodafone ES"
    assert info.line_type == "voip"
    assert info.mobile_country_code == "214"


def test_solo_pide_line_type_intelligence_nunca_caller_name():
    resp = MagicMock()
    resp.json.return_value = {"line_type_intelligence": {}}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.twilio_account_sid", "AC123"), \
         patch("app.core.config.settings.twilio_auth_token", "secret"), \
         patch("app.services.twilio_lookup_service.requests.get", return_value=resp) as mock_get:
        twilio_lookup_service.get_carrier_intelligence("+34600123456")

    fields_param = mock_get.call_args.kwargs["params"]["Fields"]
    assert fields_param == "line_type_intelligence"
    assert "caller_name" not in fields_param
    assert "identity_match" not in fields_param
