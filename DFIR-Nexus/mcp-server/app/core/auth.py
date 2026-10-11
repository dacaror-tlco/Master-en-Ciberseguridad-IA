"""
Autenticación del MCP Server contra el backend de Casos.

Inicia sesión una vez (usuario de servicio, nunca un analista humano — ver
.env.example) y guarda el JWT ÚNICAMENTE en memoria de este proceso: nunca
en disco, nunca en logs. Casos no tiene endpoint de refresh
(JWT_EXPIRE_MINUTES=120 en backend/app/core/config.py): si una petición
recibe 401, se reintenta el login una única vez y se repite esa petición;
si vuelve a fallar, el error sube tal cual a quien llamó — insistir más no
serviría, porque el sistema no tiene otra forma de renovar el token.

Desde la Fase 2C, esta MISMA sesión (un solo login, un solo JWT) también
autentica peticiones a Timeline e Informes: los 5 backends verifican el
mismo `JWT_SECRET` compartido (confirmado en la auditoría de arquitectura
MCP), así que solo Casos necesita emitir el token — `request()` acepta un
`client` opcional para dirigir la petición a cualquier backend sin volver
a autenticarse por separado en cada uno.
"""

from __future__ import annotations

import httpx

from .config import settings


class CasosAuthError(Exception):
    """Fallo de autenticación contra Casos (credenciales inválidas,
    backend inalcanzable, etc.). El mensaje nunca incluye la contraseña ni
    el JWT."""


class CasosSession:
    """Una sesión autenticada hacia Casos, reutilizada durante toda la
    vida del proceso del MCP Server."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        # Con MCP_ACCESS_TOKEN el token viene dado y nunca se inicia sesión
        # (ver config.py). Sin él, el comportamiento de siempre.
        self._token_fijo = bool(settings.MCP_ACCESS_TOKEN)
        self._token: str | None = settings.MCP_ACCESS_TOKEN or None

    async def _login(self) -> None:
        try:
            response = await self._client.post(
                "/auth/login",
                json={
                    "email": settings.MCP_SERVICE_EMAIL,
                    "password": settings.MCP_SERVICE_PASSWORD,
                },
            )
        except httpx.RequestError as exc:
            raise CasosAuthError(
                f"No se ha podido conectar con Casos para autenticar: {exc}"
            ) from exc

        if response.status_code == 401:
            raise CasosAuthError(
                "Casos ha rechazado las credenciales del usuario de servicio (401)."
            )
        if response.status_code != 200:
            # `raise_for_status()` lanzaría aquí `httpx.HTTPStatusError`, que
            # NINGÚN llamador de este método captura (ver `_peticion_segura`
            # en app/main.py: solo captura `CasosAuthError` y
            # `httpx.RequestError`, que no incluye `HTTPStatusError` — son
            # subclases hermanas de `httpx.HTTPError`, no una de la otra).
            # Sin este chequeo explícito, cualquier fallo de Casos al
            # autenticar que no sea 401 (p. ej. un 500 transitorio) tumbaba
            # la tool con una excepción sin envolver en vez de un ToolError
            # claro — auditoría final, Fase 2A-2I.
            raise CasosAuthError(
                f"Casos ha respondido con un error inesperado ({response.status_code}) al "
                "intentar autenticar el usuario de servicio."
            )
        self._token = response.json()["access_token"]

    async def request(
        self, method: str, path: str, *, client: httpx.AsyncClient | None = None, **kwargs: object
    ) -> httpx.Response:
        """Petición autenticada, con un único reintento tras un 401.

        Si todavía no hay token (primera llamada del proceso), inicia
        sesión antes de pedir nada. Si el backend devuelve 401 (token
        caducado o revocado), se vuelve a autenticar UNA vez y se repite
        la petición; un segundo 401 se devuelve tal cual a quien llamó.

        `client` es opcional: sin él, se usa el cliente de Casos (mismo
        comportamiento de siempre, sin cambios). Pasando el cliente de
        Timeline o Informes, la petición se dirige a ese backend con el
        mismo JWT ya obtenido — el login siempre es contra Casos, nunca
        contra el backend de destino.
        """
        objetivo = client if client is not None else self._client

        if self._token is None:
            await self._login()

        response = await objetivo.request(method, path, headers=self._auth_headers(), **kwargs)
        if response.status_code == 401 and not self._token_fijo:
            await self._login()
            response = await objetivo.request(method, path, headers=self._auth_headers(), **kwargs)
        return response

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}
