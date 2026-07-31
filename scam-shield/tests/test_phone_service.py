"""
Tests del servicio de teléfono. Al ser phonenumbers una librería 100%
offline (sin red, sin API key), estos tests no necesitan ningún mock —
son deterministas de verdad, no simulados.
"""
import pytest

from app.services.phone_service import analyze_phone


def test_movil_espanol_se_reconoce_correctamente():
    info = analyze_phone("+34600123456", "ES")
    assert info.line_type == "MOBILE"
    assert info.is_valid is True
    assert info.e164 == "+34600123456"
    assert info.country_code == 34


def test_numero_sin_prefijo_usa_default_region():
    info = analyze_phone("600123456", "ES")
    assert info.e164 == "+34600123456"


def test_tarificacion_especial_espanola():
    info = analyze_phone("+34803123456", "ES")
    assert info.line_type == "PREMIUM_RATE"


def test_voip_reino_unido():
    info = analyze_phone("+445600000000", "GB")
    assert info.line_type == "VOIP"


def test_numero_claramente_invalido_no_lanza_excepcion():
    info = analyze_phone("123", "ES")
    assert info.is_valid is False


def test_texto_no_telefonico_lanza_value_error():
    with pytest.raises(ValueError):
        analyze_phone("esto no es un teléfono", "ES")


def test_formato_internacional_se_rellena():
    info = analyze_phone("+34600123456", "ES")
    assert "600" in info.international_format
    assert info.national_format
