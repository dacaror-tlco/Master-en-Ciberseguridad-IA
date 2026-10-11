import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Rol(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class AuthEvento(str, enum.Enum):
    """Eventos que deja auth_audit_log. No se audita ningún GET ni
    operación normal de lectura, ni cambios de `nombre` (ver propuesta de
    identidad, sección 14).

    CONTRASENA_CAMBIADA (pantalla de Perfil): a diferencia de un admin
    reseteando la contraseña de OTRO usuario vía PUT /auth/users/{id}
    (deliberadamente sin evento propio, ver esa misma sección 14), un
    usuario cambiando SU PROPIA contraseña sí es un evento de seguridad
    con valor real para su propio historial — por eso se añade aquí y no
    junto a los demás.
    """

    LOGIN_EXITOSO = "login_exitoso"
    LOGIN_FALLIDO = "login_fallido"
    USUARIO_CREADO = "usuario_creado"
    USUARIO_DESACTIVADO = "usuario_desactivado"
    USUARIO_REACTIVADO = "usuario_reactivado"
    ROL_CAMBIADO = "rol_cambiado"
    CONTRASENA_CAMBIADA = "contrasena_cambiada"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Nunca la contraseña en claro: solo su hash Argon2id (ver security.py).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[Rol] = mapped_column(
        Enum(Rol, native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=Rol.ANALYST,
    )
    # Borrado lógico, mismo patrón que Case/Evidence: un usuario nunca se
    # borra físicamente, solo se desactiva (pierde acceso, conserva su
    # historial de auditoría como actor de acciones pasadas).
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuthAuditLog(Base):
    """
    Rastro de auditoría de identidad/acceso — deliberadamente SEPARADO de
    `case_audit_log`: un login o un cambio de rol no son un hecho sobre un
    caso concreto, no tienen `case_id` al que adjuntarse. Ver propuesta de
    identidad, sección 14.
    """

    __tablename__ = "auth_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evento: Mapped[AuthEvento] = mapped_column(
        Enum(AuthEvento, native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Usuario afectado por la acción (el que se crea/desactiva/reactiva/al
    # que se le cambia el rol, o el que intenta iniciar sesión). NULL si el
    # login falló porque el email no corresponde a ningún usuario.
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Quién realiza la acción: el propio usuario en un login, o el admin
    # que crea/modifica a otro. NULL en un login fallido con email
    # inexistente (no hay ninguna identidad real detrás todavía).
    actor_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    detalle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
