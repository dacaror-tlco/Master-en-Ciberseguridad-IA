from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.auth.models import AuthEvento, Rol


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos, para que el frontend pueda anticipar la expiración


class UserBase(BaseModel):
    nombre: str
    email: str


class UserCreate(UserBase):
    password: str
    rol: Rol = Rol.ANALYST


class UserUpdate(BaseModel):
    """
    Parcial (solo se aplican los campos enviados, exclude_unset — mismo
    patrón que CaseUpdate/EvidenceUpdate). Los guardarraíles de
    auto-protección (no dejar el sistema sin admins, no auto-desactivarse)
    se aplican en service.update_user, no aquí: este schema solo define
    QUÉ se puede enviar, no si es seguro aplicarlo para este usuario
    concreto en este momento.
    """

    nombre: str | None = None
    password: str | None = None
    rol: Rol | None = None
    activo: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rol: Rol
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    ultimo_login: datetime | None


class ChangePasswordRequest(BaseModel):
    """PUT /auth/me/password. El usuario se identifica siempre por el
    `sub` del JWT (ver dependencies.get_current_user) — este schema
    deliberadamente no lleva ningún `user_id`, así que no hay forma de
    pedir un cambio para otra cuenta manipulando el body."""

    contrasena_actual: str
    contrasena_nueva: str
    confirmacion_contrasena_nueva: str


class AuthAuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evento: AuthEvento
    user_id: int | None
    actor_user_id: int | None
    detalle: dict | None
    creado_en: datetime
