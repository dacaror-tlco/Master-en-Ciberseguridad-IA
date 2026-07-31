"""
Servicio de análisis de números de teléfono.

Usa la librería `phonenumbers` (el port en Python de libphonenumber, la
misma base de datos que usa Android/Chrome para validar teléfonos). Es
gratuita y funciona completamente offline — no hay llamada de red, no hay
límite de cuota, no hace falta ninguna API key.

El dato más valioso para detectar estafas no es "es un número válido",
sino el TIPO DE LÍNEA: un número de tarificación especial o VoIP es una
señal mucho más fuerte que la mera validez del formato.
"""
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    carrier,
    format_number,
    geocoder,
    is_possible_number,
    is_valid_number,
    number_type,
    parse as parse_phone_number,
    region_code_for_number,
)
from phonenumbers import timezone as phone_timezone

from app.schemas.phone_analysis import PhoneInfo

_LINE_TYPE_NAMES = {
    PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    PhoneNumberType.MOBILE: "MOBILE",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    PhoneNumberType.SHARED_COST: "SHARED_COST",
    PhoneNumberType.VOIP: "VOIP",
    PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    PhoneNumberType.PAGER: "PAGER",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    PhoneNumberType.UNKNOWN: "UNKNOWN",
}


def analyze_phone(raw_phone: str, default_region: str = "ES") -> PhoneInfo:
    try:
        parsed = parse_phone_number(raw_phone, default_region.upper())
    except NumberParseException as exc:
        raise ValueError(f"No se pudo interpretar '{raw_phone}' como un número de teléfono: {exc}")

    line_type = _LINE_TYPE_NAMES.get(number_type(parsed), "UNKNOWN")
    country = region_code_for_number(parsed)

    return PhoneInfo(
        e164=format_number(parsed, PhoneNumberFormat.E164),
        international_format=format_number(parsed, PhoneNumberFormat.INTERNATIONAL),
        national_format=format_number(parsed, PhoneNumberFormat.NATIONAL),
        country_code=parsed.country_code,
        country_name=country,
        region_description=geocoder.description_for_number(parsed, "es") or None,
        carrier=carrier.name_for_number(parsed, "es") or None,
        line_type=line_type,
        is_valid=is_valid_number(parsed),
        is_possible=is_possible_number(parsed),
        timezones=list(phone_timezone.time_zones_for_number(parsed)),
    )
