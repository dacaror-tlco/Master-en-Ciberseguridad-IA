"""
Dependencia FastAPI que protege las rutas de este backend — DUPLICADA, no
importada, de la misma pieza en Casos. Sin tabla `users` propia, este
backend no puede comprobar si el usuario sigue activo: confía en lo que el
JWT dice hasta que caduque (la revocación inmediata queda fuera de
alcance). Solo `get_current_user`: Tracking no tiene ningún endpoint que
exija rol admin (ver matriz de permisos, Fase 4).

Única diferencia con `development`: el interruptor
`TRACKING_AUTH_DESACTIVADA`. Allí el frontend único trae pantalla de login
y siempre hay token; este módulo también se arranca SUELTO (ver
start-dev.ps1 y el Dockerfile), y entonces no hay ninguna forma de
conseguir uno, así que la aplicación entera sería un 401. El interruptor
existe para ese caso y solo para ese: por defecto la autenticación es
OBLIGATORIA, hay que pedir explícitamente lo contrario, y el arranque lo
avisa en el log (ver app/main.py).
"""
from __future__ import annotations

import os

from fastapi import HTTPException, Request, status

from app.modules.auth.security import TokenExpiradoError, TokenInvalidoError, decodificar_token

_VALORES_AFIRMATIVOS = {"1", "true", "si", "sí", "yes"}

# Identidad que se asume cuando la autenticación está desactivada. No es un
# usuario real y no otorga nada: en este backend no hay endpoints de admin.
USUARIO_SIN_AUTENTICACION = {"sub": None, "role": "analyst", "autenticacion": "desactivada"}


def autenticacion_desactivada() -> bool:
    """Se consulta en cada petición (no al importar) para que los tests
    puedan probar los dos modos sin recargar la aplicación."""
    return os.environ.get("TRACKING_AUTH_DESACTIVADA", "").strip().lower() in _VALORES_AFIRMATIVOS


def get_current_user(request: Request) -> dict:
    if autenticacion_desactivada():
        return USUARIO_SIN_AUTENTICACION

    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    token = header.removeprefix("Bearer ").strip()
    try:
        return decodificar_token(token)
    except TokenExpiradoError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except TokenInvalidoError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
