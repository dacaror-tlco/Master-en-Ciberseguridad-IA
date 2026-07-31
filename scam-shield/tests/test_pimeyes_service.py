from unittest.mock import MagicMock, patch

import pytest

from app.services import pimeyes_service


def test_sin_api_key_lanza_runtimeerror():
    with patch("app.core.config.settings.pimeyes_api_key", ""):
        with pytest.raises(RuntimeError, match="PIMEYES_API_KEY"):
            pimeyes_service.search_face(b"fake-bytes")


def test_busqueda_exitosa_parsea_resultados():
    resp = MagicMock()
    resp.json.return_value = {
        "matches": [
            {"url": "https://otrared.example/perfil-falso", "page_title": "Perfil falso", "thumbnail_url": "https://otrared.example/t.jpg", "confidence": 0.94},
        ]
    }
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.pimeyes_api_key", "fake-key"), \
         patch("app.services.pimeyes_service.requests.post", return_value=resp):
        matches = pimeyes_service.search_face(b"fake-bytes")

    assert len(matches) == 1
    assert matches[0].url == "https://otrared.example/perfil-falso"
    assert matches[0].confidence == 0.94


def test_resultados_sin_url_se_descartan():
    resp = MagicMock()
    resp.json.return_value = {"matches": [{"page_title": "Sin url"}]}
    resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.pimeyes_api_key", "fake-key"), \
         patch("app.services.pimeyes_service.requests.post", return_value=resp):
        matches = pimeyes_service.search_face(b"fake-bytes")

    assert matches == []
