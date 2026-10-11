"""
Servicio de búsqueda inversa de imagen vía SerpApi (motor `google_reverse_image`).

Limitación real de la API, no evitable con más código: SerpApi/Google no
aceptan subir los bytes de la imagen directamente, exigen una URL pública
donde puedan descargarla ellos. Por eso `reverse_image_search` recibe una
`image_url` ya construida por quien la llama (ver
`app/api/routes/image_analysis.py`, que usa `image_cache.create_preview_token`
+ `settings.public_base_url` para montarla) — este servicio no sabe nada
de cachés ni de tokens, solo hace la llamada HTTP.

Fiabilidad del motor `google_reverse_image`, no de este código (diagnosticado
a fondo el 2026-08-02 tras timeouts persistentes en producción): la propia
SerpApi publica en https://serpapi.com/status/google_reverse_image una tasa
de éxito de ~67% y un tiempo de respuesta MEDIO de ~10.6s sobre los últimos
30 días — confirmado reproduciendo el cuelgue (>40s sin respuesta) desde dos
redes distintas, con una clave válida y una imagen de control ajena a este
proyecto, descartando así clave/cuenta/Cloudflare/red del contenedor como
causa. Con esos números, timeouts ocasionales (o incluso frecuentes) en este
motor son esperables y no indican un problema en `scam-shield` ni en su
despliegue — igual que crt.sh o Wayback Machine, pero con peor fiabilidad
todavía. Quien llame a `reverse_image_search` ya lo trata como opcional
(try/except que degrada sin tumbar el resto del análisis).
"""
import requests

from app.core.config import settings
from app.modules.osint.image.schemas import ReverseImageMatch

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
        # 60s, no 30s: SerpApi publica ~10.6s de media para este motor en concreto, con
        # cola larga hacia peticiones mucho más lentas (ver docstring del módulo) — 30s
        # descartaba de forma rutinaria búsquedas que habrían acabado bien un poco más tarde.
        timeout=60,
    )
    if not resp.ok:
        # No usamos resp.raise_for_status(): su mensaje incluye la URL completa de la
        # petición, y con ella la api_key en texto plano — se filtraría en cualquier log
        # o mensaje de error que se comparta (ya pasó una vez depurando este servicio).
        raise RuntimeError(
            f"SerpApi respondió {resp.status_code} {resp.reason} — revisa el estado de la "
            "cuenta/clave en https://serpapi.com/manage-api-key"
        )
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
