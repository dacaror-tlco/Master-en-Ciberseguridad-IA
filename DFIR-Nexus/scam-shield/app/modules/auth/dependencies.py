"""
Dependencia FastAPI para proteger rutas de este backend — DUPLICADA,
no importada, de la misma pieza en Casos (ver security.py de este mismo
módulo). Sin tabla `users` propia, este backend no puede comprobar si el
usuario sigue activo (eso solo lo sabe Casos): confía en lo que el JWT
dice en el momento de emitirse, hasta que caduque — revocación inmediata
queda fuera de alcance en esta fase (ver propuesta de identidad y
acceso).

Solo hay `get_current_user`, no `require_admin`: OSINT no tiene ningún
endpoint que exija admin (ver matriz de permisos, Fase 4) — todo lo que
está autenticado aquí lo está para cualquiera de los dos roles.
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
