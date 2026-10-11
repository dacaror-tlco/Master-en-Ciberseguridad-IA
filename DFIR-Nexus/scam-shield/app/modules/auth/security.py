"""
Verificación de JWT (HS256) — DUPLICADO deliberadamente, no importado, del
mismo fichero en el backend de Casos (autoridad de identidad, dueño de
`users` y de emitir el token). Este backend nunca emite JWT, solo los
valida: mismo JWT_SECRET (compartido vía .env, igual que ya se comparten
las credenciales de MySQL), mismo algoritmo, mismo contrato de payload
(`sub`, `role`, `iat`, `exp`). Ver propuesta de identidad y acceso,
"arquitectura preparada para futuras ampliaciones" — cada backend valida
localmente, sin importar código de otro backend ni crear una librería
compartida entre ellos.
"""
import jwt

from app.core.config import settings


class TokenInvalidoError(Exception):
    pass


class TokenExpiradoError(Exception):
    pass


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiradoError()
    except jwt.InvalidTokenError:
        raise TokenInvalidoError()
