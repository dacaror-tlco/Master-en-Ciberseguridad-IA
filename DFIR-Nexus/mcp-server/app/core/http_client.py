"""
Clientes HTTP compartidos hacia los backends de Nexus.

Un único `httpx.AsyncClient` por backend para todo el proceso (reutiliza
conexiones), con `base_url` y timeout fijos. `casos_session` añade el JWT
a cada petición (ver auth.py) y sabe autenticarse; `timeline_client`,
`informes_client`, `tracking_client` y `osint_client` son clientes HTTP
normales, sin lógica de auth propia — se usan siempre a través de
`casos_session.request(..., client=...)`, nunca solos, para que el JWT y
el reintento ante 401 se apliquen igual en los cinco backends. Es el
único punto del MCP Server que sabe hablar HTTP con ellos — las tools
nunca construyen la URL a mano.
"""

from __future__ import annotations

import httpx

from .auth import CasosSession
from .config import settings

_TIMEOUT_SECONDS = 10.0

# Un único contexto TLS para los cinco clientes. Cada `AsyncClient` que se
# crea sin él carga por su cuenta el almacén de certificados raíz, y eso es
# lo más lento de arrancar este proceso: medido en Windows, 4,4 s de 7,2 se
# iban aquí. Importa porque el asistente de Informes lanza un proceso MCP por
# pregunta. Misma verificación de certificados que antes, cargada una vez.
_tls = httpx.create_ssl_context()

_casos_client = httpx.AsyncClient(base_url=settings.CASOS_BASE_URL, timeout=_TIMEOUT_SECONDS, verify=_tls)
timeline_client = httpx.AsyncClient(base_url=settings.TIMELINE_BASE_URL, timeout=_TIMEOUT_SECONDS, verify=_tls)
informes_client = httpx.AsyncClient(base_url=settings.INFORMES_BASE_URL, timeout=_TIMEOUT_SECONDS, verify=_tls)
tracking_client = httpx.AsyncClient(base_url=settings.TRACKING_BASE_URL, timeout=_TIMEOUT_SECONDS, verify=_tls)
osint_client = httpx.AsyncClient(base_url=settings.OSINT_BASE_URL, timeout=_TIMEOUT_SECONDS, verify=_tls)

casos_session = CasosSession(_casos_client)
