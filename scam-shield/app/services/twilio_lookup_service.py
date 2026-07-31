"""
Servicio de consulta a Twilio Lookup v2: https://www.twilio.com/docs/lookup/v2-api

Twilio ofrece varios "add-ons" opcionales vía el parámetro `Fields`. Aquí
SOLO se pide `line_type_intelligence` (carrier y tipo de línea en tiempo
real, vía HLR) — a propósito NUNCA se piden `caller_name` (CNAM, nombre
del titular) ni `identity_match` (verifica nombre/dirección/fecha de
nacimiento), que sí revelan o confirman la identidad de la persona, la
misma línea que ya trazamos en el resto del proyecto (ver README, módulos
de teléfono e imagen).

`line_type_intelligence` es valioso precisamente porque completa el hueco
que la librería offline `phonenumbers` no puede cubrir: esta consulta en
tiempo real al operador, así que detecta números portados o VoIP moderno
que la base de datos estática de libphonenumber no tiene catalogado.

Es la única integración de PAGO de esta herramienta (sin tier gratuito) —
por eso, a diferencia del resto, solo se activa si el usuario configura
explícitamente sus credenciales de Twilio en `.env`.
"""
import requests
from requests.auth import HTTPBasicAuth

from app.core.config import settings
from app.schemas.phone_analysis import CarrierIntelligenceInfo

_LOOKUP_URL = "https://lookups.twilio.com/v2/PhoneNumbers"


def get_carrier_intelligence(e164_phone: str) -> CarrierIntelligenceInfo:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError(
            "No hay TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN configuradas. Este es un servicio de PAGO "
            "de Twilio (https://www.twilio.com/lookup, sin tier gratuito) — solo hace falta "
            "configurarlo si contratas el servicio; añade ambas variables a tu archivo .env"
        )

    resp = requests.get(
        f"{_LOOKUP_URL}/{e164_phone}",
        params={"Fields": "line_type_intelligence"},
        auth=HTTPBasicAuth(settings.twilio_account_sid, settings.twilio_auth_token),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    intelligence = data.get("line_type_intelligence") or {}
    return CarrierIntelligenceInfo(
        carrier_name=intelligence.get("carrier_name"),
        line_type=intelligence.get("type"),
        mobile_country_code=intelligence.get("mobile_country_code"),
        mobile_network_code=intelligence.get("mobile_network_code"),
    )
