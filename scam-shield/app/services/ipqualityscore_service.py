"""
Servicio de consulta a IPQualityScore (validación de teléfono orientada a
prevención de fraude): https://www.ipqualityscore.com/documentation/phone-number-validation-api/overview

Su API devuelve señales de comportamiento (fraud_score, VOIP, prepaid,
recent_abuse, leaked, spammer) pero TAMBIÉN un campo `name` con el nombre
del titular o de la empresa asociada al número — la documentación oficial
lo describe literalmente como "the owner of the phone number including
first and last name or the company's name". Es la misma limitación que
Truecaller, así que a propósito NUNCA se lee ni se guarda ese campo aquí:
solo se consumen las señales de comportamiento agregado, el mismo
principio que ya aplicamos con OpenSpam/VirusTotal (consenso de
reputación, no vigilancia de personas).
"""
import requests

from app.core.config import settings
from app.schemas.phone_analysis import FraudScoreInfo

_IPQS_URL = "https://www.ipqualityscore.com/api/json/phone"


def get_fraud_score(e164_phone: str) -> FraudScoreInfo:
    if not settings.ipqualityscore_api_key:
        raise RuntimeError(
            "No hay IPQUALITYSCORE_API_KEY configurada. Consigue una gratuita en "
            "https://www.ipqualityscore.com/create-account y añádela a tu archivo .env"
        )

    resp = requests.get(
        f"{_IPQS_URL}/{settings.ipqualityscore_api_key}/{e164_phone.lstrip('+')}",
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success", True):
        raise RuntimeError(data.get("message", "IPQualityScore devolvió un error"))

    # Deliberadamente NO se lee data.get("name") — ver docstring del módulo.
    return FraudScoreInfo(
        fraud_score=data.get("fraud_score"),
        voip=bool(data.get("VOIP", False)),
        prepaid=bool(data.get("prepaid", False)),
        recent_abuse=bool(data.get("recent_abuse", False)),
        leaked=bool(data.get("leaked", False)),
        spammer=bool(data.get("spammer", False)),
        active=data.get("active"),
        line_type=data.get("line_type"),
        carrier=data.get("carrier"),
    )
