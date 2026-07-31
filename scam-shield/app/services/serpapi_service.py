"""
Servicio de búsqueda inversa de imagen vía SerpApi (motor `google_reverse_image`).

Limitación real de la API, no evitable con más código: SerpApi/Google no
aceptan subir los bytes de la imagen directamente, exigen una URL pública
donde puedan descargarla ellos. Por eso `reverse_image_search` recibe una
`image_url` ya construida por quien la llama (ver
`app/api/routes/image_analysis.py`, que usa `image_cache.create_preview_token`
+ `settings.public_base_url` para montarla) — este servicio no sabe nada
de cachés ni de tokens, solo hace la llamada HTTP.
"""
import requests

from app.core.config import settings
from app.schemas.image_analysis import ReverseImageMatch

_SERPAPI_URL = "https://serpapi.com/search"


def reverse_image_search(image_url: str) -> list[ReverseImageMatch]:
    if not settings.serpapi_api_key:
        raise RuntimeError(
            "No hay SERPAPI_API_KEY configurada. Consigue una en "
            "https://serpapi.com/users/sign_up y añádela a tu archivo .env"
        )
    if not settings.public_base_url:
        raise RuntimeError(
            "No hay PUBLIC_BASE_URL configurada. SerpApi necesita descargar la imagen desde una "
            "URL pública (no acepta subida directa de bytes) — despliega la herramienta en una URL "
            "accesible desde internet (o usa un túnel tipo ngrok en local) y añade esa URL a tu .env"
        )

    resp = requests.get(
        _SERPAPI_URL,
        params={
            "engine": "google_reverse_image",
            "image_url": image_url,
            "api_key": settings.serpapi_api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("image_results") or []
    return [
        ReverseImageMatch(
            url=item.get("link"),
            page_title=item.get("title"),
            source=item.get("source"),
            thumbnail_url=item.get("thumbnail"),
        )
        for item in results
        if item.get("link")
    ]
