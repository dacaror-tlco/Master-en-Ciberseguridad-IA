"""
Hashing de contraseñas (Argon2id) y JWT (HS256). Único lugar del backend
que toca criptografía de identidad — el resto del módulo `auth` solo llama
a estas funciones, nunca a argon2/PyJWT directamente.

Argon2id en vez de bcrypt: `argon2-cffi-bindings` publica wheel
manylinux para aarch64 (verificado contra PyPI antes de decidir esto —
el stack de Nexus despliega en Raspberry Pi/arm64, ver deploy/), así que
no hay riesgo de compilación nativa en el build de producción.
"""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.config import settings
from app.modules.auth.models import Rol

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


class TokenInvalidoError(Exception):
    pass


class TokenExpiradoError(Exception):
    pass


def crear_token(*, user_id: int, rol: Rol) -> str:
    """
    Payload mínimo a propósito: solo lo necesario para autorizar la
    petición (sub, role, iat, exp) — nunca email/nombre, que se obtienen
    siempre frescos vía GET /auth/me si hacen falta. Ver propuesta de
    identidad, sección 2 (JWT).
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": rol.value,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiradoError()
    except jwt.InvalidTokenError:
        raise TokenInvalidoError()
