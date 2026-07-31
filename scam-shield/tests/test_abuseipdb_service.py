from unittest.mock import MagicMock, patch

import pytest

from app.services import abuseipdb_service


def test_sin_api_key_lanza_runtimeerror():
    with patch("app.core.config.settings.abuseipdb_api_key", ""):
        with pytest.raises(RuntimeError, match="ABUSEIPDB_API_KEY"):
            abuseipdb_service.get_ip_reputation("1.2.3.4")


def test_parsea_reputacion():
    resp = MagicMock()
    resp.json.return_value = {
        "data": {
            "ipAddress": "1.2.3.4", "abuseConfidenceScore": 92, "totalReports": 40,
            "isWhitelisted": False, "isTor": True, "usageType": "Data Center/Web Hosting/Transit",
            "isp": "Some Hosting Provider", "domain": "example.com", "countryCode": "US",
            "lastReportedAt": "2026-07-01T00:00:00+00:00",
        }
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=resp):
        info = abuseipdb_service.get_ip_reputation("1.2.3.4")

    assert info.abuse_confidence_score == 92
    assert info.total_reports == 40
    assert info.is_tor is True
    assert info.isp == "Some Hosting Provider"
    assert info.country_code == "US"


def test_usa_header_key_no_query_param():
    resp = MagicMock()
    resp.json.return_value = {"data": {"ipAddress": "1.2.3.4"}}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=resp) as mock_get:
        abuseipdb_service.get_ip_reputation("1.2.3.4")

    headers = mock_get.call_args.kwargs["headers"]
    assert headers["Key"] == "fake-key"
    assert "key" not in mock_get.call_args.kwargs.get("params", {})
