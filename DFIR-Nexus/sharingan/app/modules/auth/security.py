"""
Verificación de JWT (HS256) — DUPLICADO deliberadamente, no importado, del
mismo fichero en el backend de Casos (autoridad de identidad, dueño de
`users` y de emitir el token). Este backend nunca emite JWT, solo los
valida: mismo JWT_SECRET (compartido vía .env), mismo algoritmo, mismo
contrato de payload (`sub`, `role`, `iat`, `exp`). Sin librería compartida
entre backends: cada uno lleva su propia copia mínima.
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
