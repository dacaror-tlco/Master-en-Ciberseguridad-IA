from unittest.mock import MagicMock, patch

import pytest

from app.services import fca_register_service


def test_sin_credenciales_lanza_runtimeerror():
    with patch("app.core.config.settings.fca_api_email", ""), \
         patch("app.core.config.settings.fca_api_key", ""):
        with pytest.raises(RuntimeError, match="FCA_API_EMAIL"):
            fca_register_service.search_firm("Barclays")


def test_solo_falta_key_tambien_lanza_runtimeerror():
    with patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", ""):
        with pytest.raises(RuntimeError, match="FCA_API_EMAIL"):
            fca_register_service.search_firm("Barclays")


def test_parsea_resultados():
    """
    Regresión: la respuesta real de la API usa la clave "Data" (mayúscula),
    no "data" como sugería la documentación de la librería de referencia
    consultada — confirmado probando contra la API real. Con la clave en
    minúscula el parseo nunca fallaba, simplemente devolvía siempre [].
    """
    resp = MagicMock()
    resp.json.return_value = {
        "Data": [{
            "Name": "Barclays Bank Plc (Postcode: E14 5HP)",
            "Reference Number": "122702",
            "Status": "Authorised",
            "Type of business or Individual": "Firm",
            "URL": "https://register.fca.org.uk/services/V0.1/Firm/122702",
        }],
        "Status": "FSR-API-04-01-00", "Message": "Ok. Search successful",
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=resp):
        matches = fca_register_service.search_firm("Barclays")

    assert len(matches) == 1
    assert matches[0].reference_number == "122702"
    assert matches[0].status == "Authorised"
    assert matches[0].type_of_business == "Firm"


def test_parsea_firma_no_autorizada_clon():
    """Con datos reales, la propia búsqueda ya incluye clones/no autorizadas marcadas así explícitamente."""
    resp = MagicMock()
    resp.json.return_value = {
        "Data": [{
            "Name": "Barclays Capital (clone of FCA authorised firm)",
            "Reference Number": "",
            "Status": "Unauthorised",
            "Type of business or Individual": "Unauthorised firm",
            "URL": None,
        }]
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=resp):
        matches = fca_register_service.search_firm("Barclays")

    assert matches[0].type_of_business == "Unauthorised firm"
    assert matches[0].status == "Unauthorised"


def test_usa_headers_x_auth():
    resp = MagicMock()
    resp.json.return_value = {"Data": []}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=resp) as mock_get:
        fca_register_service.search_firm("Barclays")

    headers = mock_get.call_args.kwargs["headers"]
    assert headers["X-Auth-Email"] == "yo@example.com"
    assert headers["X-Auth-Key"] == "fake-key"


def test_resultados_sin_nombre_se_descartan():
    resp = MagicMock()
    resp.json.return_value = {"Data": [{"Reference Number": "1"}]}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.fca_api_email", "yo@example.com"), \
         patch("app.core.config.settings.fca_api_key", "fake-key"), \
         patch("app.services.fca_register_service.requests.get", return_value=resp):
        matches = fca_register_service.search_firm("algo")

    assert matches == []
