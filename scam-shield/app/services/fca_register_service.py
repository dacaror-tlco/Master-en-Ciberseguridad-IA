"""
Servicio de consulta al registro público de la FCA (Financial Conduct
Authority, Reino Unido): https://register.fca.org.uk

A diferencia del listado de advertencias de la CNMV (una lista NEGRA de
entidades ya señaladas), esta es sobre todo una comprobación EN POSITIVO:
¿aparece esta entidad en el registro de firmas autorizadas/registradas
del regulador británico, y con qué estado?

Endpoint confirmado contra el código fuente del cliente Python de
referencia (fsrapiclient): GET .../V0.1/Search?q=<nombre>&type=firm,
headers X-Auth-Email/X-Auth-Key (API gratuita, registro en
https://register.fca.org.uk/Developer/s/).

**Ojo con la documentación de terceros — la forma REAL de la respuesta no
coincide con la de la librería de referencia consultada** (mismo tipo de
sorpresa que ya tuvimos con OpenSpam en el módulo de teléfono, otra vez
confirmado probando contra la API real, no fiándonos de la doc): la lista
de resultados va en la clave `"Data"` (con D mayúscula), no `"data"` —
con la clave en minúscula el parseo nunca lanzaba error, simplemente
devolvía siempre una lista vacía en silencio.

Además, probando con datos reales apareció algo mejor de lo esperado: la
propia búsqueda SÍ incluye entradas explícitas de firmas clonadas/no
autorizadas, con `"Type of business or Individual": "Unauthorised firm"`
y nombres tan directos como "Barclays Capital (clone of FCA authorised
firm)" — es decir, sí hay señal de "lista negra" dentro de esta misma
búsqueda, no hace falta un endpoint aparte. Por eso `type_of_business` se
captura como campo propio en `FcaMatch`, y es la señal principal en
`cnmv_risk_engine.py` (más fuerte que solo mirar `Status`).
"""
import requests

from app.core.config import settings
from app.schemas.cnmv import FcaMatch

_SEARCH_URL = "https://register.fca.org.uk/services/V0.1/Search"


def search_firm(query: str) -> list[FcaMatch]:
    if not settings.fca_api_email or not settings.fca_api_key:
        raise RuntimeError(
            "No hay FCA_API_EMAIL/FCA_API_KEY configuradas. Regístrate gratis en "
            "https://register.fca.org.uk/Developer/s/ y añade ambas variables a tu archivo .env"
        )

    resp = requests.get(
        _SEARCH_URL,
        params={"q": query, "type": "firm"},
        headers={
            "X-Auth-Email": settings.fca_api_email,
            "X-Auth-Key": settings.fca_api_key,
            "Accept": "application/json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = (resp.json() or {}).get("Data") or []

    return [
        FcaMatch(
            name=item.get("Name", ""),
            reference_number=item.get("Reference Number", ""),
            status=item.get("Status", ""),
            type_of_business=item.get("Type of business or Individual"),
            url=item.get("URL"),
        )
        for item in data
        if item.get("Name")
    ]
