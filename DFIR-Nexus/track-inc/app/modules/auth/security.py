"""
Verificación de JWT (HS256) — DUPLICADO deliberadamente, no importado, del
mismo fichero en el backend de Casos (autoridad de identidad, dueño de
`users` y único que emite tokens). Este backend nunca emite JWT, solo los
valida: mismo JWT_SECRET (compartido vía .env, igual que ya se comparte
DATABASE_URL — ver app/core/database.py), mismo algoritmo, mismo contrato
de payload (`sub`, `role`, `iat`, `exp`). Sin librería compartida entre
backends: cada uno lleva su propia copia mínima, que es la regla de
CLAUDE.md de bajo acoplamiento (ningún backend importa código de otro).

Fichero alineado con el de `development` (commit 9d625bd): si allí cambia
el contrato del token, aquí solo hay que traerse ese cambio.
"""
from __future__ import annotations

import os
from pathlib import Path

import jwt
from dotenv import load_dotenv

# Mismo patrón que app/core/database.py: carga el .env del módulo por ruta
# absoluta (no depende del directorio desde el que se lance uvicorn o
# pytest), sin pisar una variable que ya venga del entorno.
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)

SECRETO_POR_DEFECTO = "change_me"
JWT_SECRET = os.environ.get("JWT_SECRET", SECRETO_POR_DEFECTO)


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
