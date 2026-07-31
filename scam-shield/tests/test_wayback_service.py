from unittest.mock import MagicMock, patch

import pytest

from app.services import wayback_service


@pytest.fixture(autouse=True)
def _no_real_wayback_lookup():
    """Anula, solo en este archivo, el autouse global de conftest.py — ver test_crtsh_service.py."""
    yield


def _fake_response(rows):
    resp = MagicMock()
    resp.json.return_value = rows
    resp.raise_for_status.return_value = None
    return resp


def test_sin_capturas_da_cero():
    # Sin capturas, el CDX API devuelve solo la fila de cabecera (o lista vacía).
    header_only = _fake_response([["timestamp"]])
    with patch("app.services.wayback_service.requests.get", return_value=header_only):
        info = wayback_service.get_wayback_info("dominio-nunca-visto.xyz")

    assert info.total_snapshots == 0
    assert info.first_snapshot is None
    assert info.last_snapshot is None


def test_primera_ultima_captura_y_conteo():
    first_and_count_resp = _fake_response([["timestamp"], ["20150101000000"], ["20180601000000"], ["20200101000000"]])
    last_resp = _fake_response([["timestamp"], ["20260101120000"]])

    with patch("app.services.wayback_service.requests.get", side_effect=[first_and_count_resp, last_resp]):
        info = wayback_service.get_wayback_info("ejemplo.com")

    assert info.total_snapshots == 3
    assert info.first_snapshot.year == 2015
    assert info.last_snapshot.year == 2026


def test_pide_primero_en_orden_ascendente_y_ultimo_con_limit_negativo():
    resp = _fake_response([["timestamp"], ["20150101000000"]])
    with patch("app.services.wayback_service.requests.get", return_value=resp) as mock_get:
        wayback_service.get_wayback_info("ejemplo.com")

    first_call_params = mock_get.call_args_list[0].kwargs["params"]
    last_call_params = mock_get.call_args_list[1].kwargs["params"]
    assert first_call_params["limit"] > 0
    assert last_call_params["limit"] < 0
