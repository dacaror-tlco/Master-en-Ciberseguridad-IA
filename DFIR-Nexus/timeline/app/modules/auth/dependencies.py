"""
Dependencia FastAPI para proteger rutas de este backend — DUPLICADA,
no importada, de la misma pieza en Casos. Sin tabla `users` propia, este
backend no puede comprobar si el usuario sigue activo: confía en lo que
el JWT dice hasta que caduque (revocación inmediata queda fuera de
alcance). Solo `get_current_user`: Timeline no tiene ningún endpoint que
exija admin (ver matriz de permisos, Fase 4).
"""
from fastapi import HTTPException, Request, status

from app.modules.auth.security import TokenExpiradoError, TokenInvalidoError, decodificar_token


def get_current_user(request: Request) -> dict:
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
