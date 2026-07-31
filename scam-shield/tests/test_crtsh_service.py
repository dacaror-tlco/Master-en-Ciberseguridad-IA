from unittest.mock import MagicMock, patch

import pytest

from app.services import crtsh_service


@pytest.fixture(autouse=True)
def _no_real_crtsh_lookup():
    """
    Anula, solo en este archivo, el autouse global de conftest.py que
    sustituye `get_crtsh_info` entero por un fallo simulado (pensado para
    el resto de la suite, que no quiere red real) — aquí es justo la
    función que se está probando, con `requests.get` mockeado más abajo.
    """
    yield


def _fake_response(entries):
    resp = MagicMock()
    resp.json.return_value = entries
    resp.raise_for_status.return_value = None
    return resp


def test_extrae_y_dedupe_subdominios():
    entries = [
        {"name_value": "www.ejemplo.com\nejemplo.com"},
        {"name_value": "api.ejemplo.com"},
        {"name_value": "www.ejemplo.com"},  # duplicado en otro certificado
    ]
    with patch("app.services.crtsh_service.requests.get", return_value=_fake_response(entries)):
        info = crtsh_service.get_crtsh_info("ejemplo.com")

    assert info.subdomain_count == 2  # www + api — 'ejemplo.com' (el propio dominio) no cuenta
    assert info.subdomains == ["api.ejemplo.com", "www.ejemplo.com"]


def test_quita_prefijo_wildcard():
    entries = [{"name_value": "*.ejemplo.com"}]
    with patch("app.services.crtsh_service.requests.get", return_value=_fake_response(entries)):
        info = crtsh_service.get_crtsh_info("ejemplo.com")

    assert info.subdomains == []  # '*.ejemplo.com' sin el asterisco ES el propio dominio, no un subdominio


def test_ignora_dominios_no_relacionados():
    """crt.sh puede devolver certificados SAN que incluyan otros dominios ajenos en el mismo certificado."""
    entries = [{"name_value": "sub.ejemplo.com\notro-dominio-cualquiera.com"}]
    with patch("app.services.crtsh_service.requests.get", return_value=_fake_response(entries)):
        info = crtsh_service.get_crtsh_info("ejemplo.com")

    assert info.subdomains == ["sub.ejemplo.com"]


def test_detecta_subdominio_con_marca_suplantada():
    entries = [{"name_value": "bbva-verificacion.dominio-malo.xyz"}]
    with patch("app.services.crtsh_service.requests.get", return_value=_fake_response(entries)):
        info = crtsh_service.get_crtsh_info("dominio-malo.xyz")

    assert info.suspected_brand_subdomains == ["bbva-verificacion.dominio-malo.xyz"]


def test_sin_certificados_da_info_vacia():
    with patch("app.services.crtsh_service.requests.get", return_value=_fake_response([])):
        info = crtsh_service.get_crtsh_info("ejemplo.com")

    assert info.subdomain_count == 0
    assert info.subdomains == []
    assert info.suspected_brand_subdomains == []
