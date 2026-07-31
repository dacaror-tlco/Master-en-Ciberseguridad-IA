from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.services import image_cache


def test_put_y_get_devuelve_los_mismos_bytes():
    image_cache.put(1, b"foto-original")
    assert image_cache.get(1) == b"foto-original"


def test_get_de_case_id_inexistente_da_none():
    assert image_cache.get(999999) is None


def test_get_tras_expirar_da_none():
    image_cache.put(2, b"foto")
    future = datetime.now(timezone.utc) + timedelta(minutes=20)
    with patch("app.services.image_cache.datetime") as mock_dt:
        mock_dt.now.return_value = future
        assert image_cache.get(2) is None


def test_preview_token_se_consume_una_sola_vez():
    token = image_cache.create_preview_token(b"foto-preview")
    assert image_cache.consume_preview_token(token) == b"foto-preview"
    assert image_cache.consume_preview_token(token) is None


def test_preview_token_inexistente_da_none():
    assert image_cache.consume_preview_token("token-que-no-existe") is None
