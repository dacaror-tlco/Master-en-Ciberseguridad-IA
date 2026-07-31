"""
Servicio de consulta a OpenSpam (https://www.openspam.es).

Deliberadamente NO busca "de quién es este número" (eso es un dato
personal, y el mecanismo para conseguirlo — bases de datos de agendas de
contactos ajenas — es el mismo que usan herramientas de acoso). Lo que sí
consultamos es si OTRAS PERSONAS ya han reportado ESE NÚMERO CONCRETO
como spam, fraude o telemarketing — un reporte de comportamiento, no una
identidad. Es el mismo principio que ya aplicamos con VirusTotal (dominios)
o Chainabuse (wallets): consenso de la comunidad de seguridad, no
vigilancia de personas.

OpenSpam ofrece una API pública gratuita pensada exactamente para esto
("investigación e integraciones") y pide explícitamente NO hacer scraping
de su web, así que la usamos tal cual: https://api.openspam.es

Estructura de la respuesta REAL (confirmada con una respuesta completa
capturada de la demo de su propia web, no de la documentación — la doc
oficial no coincide con esto):
    {
      "success": true,
      "data": {
        "encontrado": true,
        "numero": {
          "telefono": "...", "total_reportes": 81, "nivel_peligro": "alto",
          "tipo_spam": "spam", "provincia": null, "operadora": "Vodafone", ...
        },
        "reportes_recientes": [...],
        "recomendacion": "..."
      }
    }
Es decir: los datos del número van DENTRO de `data.numero`, no directamente
en `data` (así lo interpretamos en las dos versiones anteriores de este
servicio, y era el motivo real de que todo diera "0 reportes"). Cuando el
número no está en su base, `data.encontrado` es `false` y `numero` es null.
"""
import requests

from app.core.config import settings
from app.schemas.phone_analysis import CommunityReportInfo

_OPENSPAM_BASE_URL = "https://api.openspam.es/api/number"


def get_community_reports(e164_phone: str) -> CommunityReportInfo:
    if not settings.openspam_api_key:
        raise RuntimeError(
            "No hay OPENSPAM_API_KEY configurada. Consigue una gratuita en "
            "https://api.openspam.es/panel y añádela a tu archivo .env"
        )

    resp = requests.get(
        f"{_OPENSPAM_BASE_URL}/{e164_phone}",
        headers={"X-API-Key": settings.openspam_api_key},
        timeout=10,
    )

    # Un número que nunca se ha reportado NO es un fallo del servicio, es el
    # resultado normal para la inmensa mayoría de números — lo tratamos como
    # "0 reportes", no como una excepción a esconder en `errors`.
    if resp.status_code == 404:
        return CommunityReportInfo(reports_count=0)

    resp.raise_for_status()
    body = resp.json()

    if not body.get("success"):
        return CommunityReportInfo(reports_count=0)

    data = body.get("data") or {}

    # "encontrado: false" es la forma real (confirmada) en que la API dice
    # "este número no está en la base de datos" con un 200 normal.
    if data.get("encontrado") is False:
        return CommunityReportInfo(reports_count=0)

    # Los datos van anidados bajo "numero". Si en algún momento la API
    # cambia y los deja planos en "data" directamente, esto lo sigue
    # soportando igual (fallback a `data` si no hay "numero").
    numero = data.get("numero")
    if not isinstance(numero, dict):
        numero = data

    reports_count = numero.get("total_reportes")
    if reports_count is None:
        reports_count = numero.get("reportes", 0)

    category = numero.get("tipo_spam") or numero.get("tipo") or numero.get("tipo_spam_amigable")
    danger_level = numero.get("nivel_peligro") or numero.get("peligro_nivel")

    return CommunityReportInfo(
        reports_count=reports_count or 0,
        category=category,
        province=numero.get("provincia"),
        danger_level=danger_level,
    )
