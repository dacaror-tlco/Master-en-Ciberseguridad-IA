from unittest.mock import MagicMock, patch

import pytest

from app.services import serpapi_service


def test_sin_api_key_lanza_runtimeerror():
    with patch("app.core.config.settings.serpapi_api_key", ""):
        with pytest.raises(RuntimeError, match="SERPAPI_API_KEY"):
            serpapi_service.reverse_image_search("https://example.com/foto.jpg")


def test_sin_public_base_url_lanza_runtimeerror():
    with patch("app.core.config.settings.serpapi_api_key", "fake-key"), \
         patch("app.core.config.settings.public_base_url", ""):
        with pytest.raises(RuntimeError, match="PUBLIC_BASE_URL"):
            serpapi_service.reverse_image_search("https://example.com/foto.jpg")


def test_busqueda_exitosa_parsea_resultados():
    resp = MagicMock()
    resp.json.return_value = {
        "image_results": [
            {"link": "https://otrared.example/perfil", "title": "Perfil de citas", "source": "otrared.example", "thumbnail": "https://otrared.example/thumb.jpg"},
            {"link": "https://stockphotos.example/foto", "title": "Foto de stock", "source": "stockphotos.example"},
        ]
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.serpapi_api_key", "fake-key"), \
         patch("app.core.config.settings.public_base_url", "https://miapp.example.com"), \
         patch("app.services.serpapi_service.requests.get", return_value=resp):
        matches = serpapi_service.reverse_image_search("https://miapp.example.com/analysis/image/preview/abc")

    assert len(matches) == 2
    assert matches[0].url == "https://otrared.example/perfil"
    assert matches[0].source == "otrared.example"


def test_resultados_sin_link_se_descartan():
    resp = MagicMock()
    resp.json.return_value = {"image_results": [{"title": "Sin link"}]}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.serpapi_api_key", "fake-key"), \
         patch("app.core.config.settings.public_base_url", "https://miapp.example.com"), \
         patch("app.services.serpapi_service.requests.get", return_value=resp):
        matches = serpapi_service.reverse_image_search("https://miapp.example.com/x")

    assert matches == []
