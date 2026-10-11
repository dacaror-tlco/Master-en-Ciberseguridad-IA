"""
Verificación de JWT (HS256) — DUPLICADO deliberadamente, no importado, del
mismo fichero en el backend de Casos (autoridad de identidad, dueño de
`users` y de emitir el token). Este backend nunca emite JWT, solo los
valida: mismo JWT_SECRET (compartido vía .env, igual que ya se comparte
DATABASE_URL — ver app/core/database.py), mismo algoritmo, mismo contrato
de payload (`sub`, `role`, `iat`, `exp`). Sin librería compartida entre
backends: cada uno lleva su propia copia mínima.
"""
from __future__ import annotations

import os
from pathlib import Path

import jwt
from dotenv import load_dotenv

# Mismo patrón que app/core/database.py: carga timeline/.env por ruta
# absoluta, sin pisar una variable que ya esté en el entorno.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

JWT_SECRET = os.environ.get("JWT_SECRET", "change_me")


class TokenInvalidoError(Exception):
    pass


class TokenExpiradoError(Exception):
    pass


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiradoError()
    except jwt.InvalidTokenError:
        raise TokenInvalidoError()
