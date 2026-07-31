"""
Servicio de consulta al buscador de entidades autorizadas de la CNMV
(https://www.cnmv.es/portal/consultas/busquedaporentidad?tipoBusqueda=ESI&lang=es).

A diferencia del listado de advertencias (`cnmv_service.py`, una lista
NEGRA), esto es una comprobación EN POSITIVO: ¿existe una entidad con ese
nombre en el registro de Empresas de Servicios de Inversión (ESI)
autorizadas a operar en España? Es el equivalente español de
`fca_register_service.py` para el Reino Unido.

Es un formulario ASP.NET clásico con post-back (`__VIEWSTATE`,
`__EVENTVALIDATION`) — probado hoy contra la web real (no de memoria) con
un patrón simple: GET para conseguir los tokens + POST con la búsqueda,
reutilizando la misma sesión (cookies). No hace falta JavaScript ni
simular el segundo post-back de "Seleccionar" (que daría el detalle
completo de una entidad concreta) — la sola existencia/ausencia de
coincidencias ya es la señal en positivo que se busca; el detalle
completo queda como posible ampliación futura.

Confirmado con datos reales al escribir esto:
- "AICHAINTRADER" (chiringuito real de la lista de advertencias) -> 0 resultados
- "Renta 4" (empresa legítima) -> 2 resultados (RENTA 4 BANCO, S.A. / RENTA 4 GESTORA, S.G.I.I.C., S.A.)
- "Barclays" -> 15 entidades reales registradas en España

Alcance actual: solo el tipo "ESI" (`tipoBusqueda=ESI`) — la CNMV tiene
otros sub-registros (bancos, IIC...) no cubiertos aquí.

Mismo aviso de fragilidad que `cnmv_service.py`: si la CNMV cambia el
HTML de este formulario, el parseo puede dejar de encontrar el `<select>`
de resultados — en ese caso falla de forma ruidosa (excepción clara en
`errors`) en vez de devolver silenciosamente "0 resultados".
"""
import requests
from bs4 import BeautifulSoup

from app.schemas.cnmv import CnmvRegisteredEntity

_SEARCH_URL = "https://www.cnmv.es/portal/consultas/busquedaporentidad?tipoBusqueda=ESI&lang=es"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ScamShield/1.0; +investigacion academica)"}
_RESULT_SELECT_NAME = "ctl00$ContentPrincipal$wuc_Entidades$lstSeleccion"
_SEARCH_FIELD_NAME = "ctl00$ContentPrincipal$txtBusqueda"
_SEARCH_BUTTON_NAME = "ctl00$ContentPrincipal$btnBuscar"


def _hidden_value(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("input", {"name": name})
    return tag["value"] if tag and tag.has_attr("value") else ""


def search_registered_entities(query: str, timeout: float = 15.0) -> list[CnmvRegisteredEntity]:
    session = requests.Session()

    resp = session.get(_SEARCH_URL, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": _hidden_value(soup, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _hidden_value(soup, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _hidden_value(soup, "__EVENTVALIDATION"),
        _SEARCH_FIELD_NAME: query,
        _SEARCH_BUTTON_NAME: "Buscar",
    }
    resp2 = session.post(_SEARCH_URL, headers=_HEADERS, data=payload, timeout=timeout)
    resp2.raise_for_status()
    soup2 = BeautifulSoup(resp2.text, "html.parser")

    select = soup2.find("select", {"name": _RESULT_SELECT_NAME})
    if select is None:
        if "no se han encontrado resultados" in resp2.text.lower():
            return []
        raise RuntimeError(
            "No se encontró el formulario de resultados en el registro de entidades de la CNMV — "
            "es posible que hayan cambiado la estructura de su web (ver el aviso en la cabecera de "
            "cnmv_registry_service.py)."
        )

    return [
        CnmvRegisteredEntity(code=option["value"], name=option.get_text(strip=True))
        for option in select.find_all("option")
        if option.get("value")
    ]
