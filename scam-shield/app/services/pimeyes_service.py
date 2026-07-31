"""
Servicio de búsqueda de reconocimiento facial vía PimEyes.

INTEGRACIÓN DE REFERENCIA, no verificada contra el contrato real de la API:
a diferencia de SerpApi (autoservicio, documentación pública), el acceso a
la API de negocio de PimEyes requiere solicitud/aprobación previa, y no
había documentación pública fiable disponible al escribir esto. La llamada
de abajo (`POST` multipart con `Authorization: Bearer`, respuesta con una
lista `matches`) es la forma habitual en APIs de este tipo, pero **hay que
ajustarla** en cuanto se tenga acceso real y su documentación oficial —
el endpoint, el nombre de los campos del multipart, y la forma exacta del
JSON de respuesta pueden no coincidir. El resto del sistema (schema, motor
de riesgo, persistencia, cadena de custodia) no depende de acertar esto a
la primera: solo hay que ajustar el parseo de `_parse_matches` cuando se
confirme el formato real.

Ver también `app/models/facial_search_case.py` y la sección "Reconocimiento
facial (PimEyes) — uso acotado" del README para las salvaguardas legales
con las que se envuelve esta llamada (nunca se dispara automáticamente
desde el análisis normal de una imagen).
"""
import requests

from app.core.config import settings
from app.schemas.image_analysis import FacialSearchMatch

_PIMEYES_API_URL = "https://api.pimeyes.com/v1/search"  # placeholder — ajustar al endpoint real


def _parse_matches(data: dict) -> list[FacialSearchMatch]:
    results = data.get("matches") or []
    return [
        FacialSearchMatch(
            url=item.get("url"),
            page_title=item.get("page_title"),
            thumbnail_url=item.get("thumbnail_url"),
            confidence=item.get("confidence"),
        )
        for item in results
        if item.get("url")
    ]


def search_face(raw_bytes: bytes) -> list[FacialSearchMatch]:
    if not settings.pimeyes_api_key:
        raise RuntimeError(
            "No hay PIMEYES_API_KEY configurada. El acceso a la API de PimEyes requiere solicitud "
            "de negocio aprobada por PimEyes (no es autoservicio) — una vez aprobado, añade la "
            "clave a tu archivo .env"
        )

    resp = requests.post(
        _PIMEYES_API_URL,
        files={"image": raw_bytes},
        headers={"Authorization": f"Bearer {settings.pimeyes_api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return _parse_matches(resp.json())
