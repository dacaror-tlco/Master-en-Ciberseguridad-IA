from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth import repository
from app.modules.auth.models import AuthAuditLog, AuthEvento, Rol, User
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest, UserCreate, UserUpdate
from app.modules.auth.security import crear_token, hash_password, verify_password


class InvalidCredentialsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class EmailYaRegistradoError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Ya existe un usuario con el email {email!r}")


class UltimoAdminError(Exception):
    """El cambio dejaría el sistema sin ningún administrador activo."""


class AutoDesactivacionError(Exception):
    """Un admin no puede desactivar su propia cuenta."""


class CurrentPasswordIncorrectError(Exception):
    """La contraseña actual proporcionada no coincide con la registrada."""


class PasswordConfirmationMismatchError(Exception):
    """La nueva contraseña y su confirmación no coinciden."""


class PasswordTooShortError(Exception):
    """La nueva contraseña no cumple la longitud mínima."""


def authenticate(db: Session, data: LoginRequest) -> tuple[str, int, User]:
    """
    Devuelve (access_token, expires_in, user) o lanza InvalidCredentialsError.
    Registra siempre en auth_audit_log, tanto el éxito como cada fallo —
    ver propuesta de identidad, sección 14. La contraseña introducida
    nunca se escribe en `detalle` ni en ningún log, en ningún caso.
    """
    user = repository.get_by_email(db, data.email)

    if user is None:
        repository.add_audit_entry(
            db,
            evento=AuthEvento.LOGIN_FALLIDO,
            user_id=None,
            actor_user_id=None,
            detalle={"email_intentado": data.email},
        )
        raise InvalidCredentialsError()

    if not user.activo or not verify_password(data.password, user.password_hash):
        repository.add_audit_entry(
            db,
            evento=AuthEvento.LOGIN_FALLIDO,
            user_id=user.id,
            actor_user_id=user.id,
            detalle={"email_intentado": data.email},
        )
        raise InvalidCredentialsError()

    repository.registrar_ultimo_login(db, user)
    repository.add_audit_entry(
        db, evento=AuthEvento.LOGIN_EXITOSO, user_id=user.id, actor_user_id=user.id
    )

    token = crear_token(user_id=user.id, rol=user.rol)
    return token, settings.JWT_EXPIRE_MINUTES * 60, user


def get_user(db: Session, user_id: int) -> User:
    user = repository.get_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError(user_id)
    return user


def list_users(db: Session) -> list[User]:
    return repository.list_users(db)


def create_user(db: Session, data: UserCreate, *, actor: User) -> User:
    if repository.get_by_email(db, data.email) is not None:
        raise EmailYaRegistradoError(data.email)

    user = repository.create_user(db, data, hash_password(data.password))
    repository.add_audit_entry(
        db,
        evento=AuthEvento.USUARIO_CREADO,
        user_id=user.id,
        actor_user_id=actor.id,
        detalle={"email": user.email, "rol": user.rol.value},
    )
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, *, actor: User) -> User:
    """
    Aplica los guardarraíles de la propuesta de identidad (sección 13),
    en este orden, ANTES de tocar nada:

    1. Auto-desactivación bloqueada siempre (activo=False sobre uno mismo).
    2. Nunca cero administradores activos tras el cambio (desactivar o
       degradar a un admin — a uno mismo o a otro — cuando sería el
       último que queda).

    Genera una entrada de auth_audit_log POR CADA evento relevante que el
    PUT produzca (puede ser más de uno en la misma llamada) — mismo
    patrón que case_audit_log ya usa cuando un PUT /cases/{id} toca varios
    campos a la vez.
    """
    user = get_user(db, user_id)
    campos = data.model_dump(exclude_unset=True)

    es_auto_modificacion = user.id == actor.id

    if es_auto_modificacion and campos.get("activo") is False:
        raise AutoDesactivacionError()

    rol_nuevo = campos.get("rol")
    activo_nuevo = campos.get("activo")
    degradando_admin = user.rol == Rol.ADMIN and rol_nuevo is not None and rol_nuevo != Rol.ADMIN
    desactivando_admin = user.rol == Rol.ADMIN and user.activo and activo_nuevo is False
    if degradando_admin or desactivando_admin:
        if repository.count_admins_activos(db, excluir_id=user.id) == 0:
            raise UltimoAdminError()

    rol_anterior = user.rol
    activo_anterior = user.activo

    if "password" in campos:
        campos["password_hash"] = hash_password(campos.pop("password"))

    updated = repository.apply_update(db, user, campos)

    if "rol" in campos and campos["rol"] != rol_anterior:
        repository.add_audit_entry(
            db,
            evento=AuthEvento.ROL_CAMBIADO,
            user_id=updated.id,
            actor_user_id=actor.id,
            detalle={"de": rol_anterior.value, "a": campos["rol"].value},
        )
    if "activo" in campos and campos["activo"] != activo_anterior:
        evento = AuthEvento.USUARIO_REACTIVADO if campos["activo"] else AuthEvento.USUARIO_DESACTIVADO
        repository.add_audit_entry(
            db, evento=evento, user_id=updated.id, actor_user_id=actor.id
        )

    return updated


LONGITUD_MINIMA_PASSWORD = 8


def change_own_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    """
    Pantalla de Perfil — cambio de la PROPIA contraseña. `user` viene
    siempre de get_current_user (JWT), nunca de un id que decida el
    llamador: no existe ninguna vía, en este endpoint, para pedir el
    cambio de la contraseña de otra cuenta.

    Comprobaciones baratas (forma del request) antes que la cara
    (verify_password, Argon2id) — así una confirmación que no coincide o
    una contraseña demasiado corta no gastan un hash innecesario.
    """
    if data.contrasena_nueva != data.confirmacion_contrasena_nueva:
        raise PasswordConfirmationMismatchError()
    if len(data.contrasena_nueva) < LONGITUD_MINIMA_PASSWORD:
        raise PasswordTooShortError()
    if not verify_password(data.contrasena_actual, user.password_hash):
        raise CurrentPasswordIncorrectError()

    repository.apply_update(db, user, {"password_hash": hash_password(data.contrasena_nueva)})
    repository.add_audit_entry(
        db, evento=AuthEvento.CONTRASENA_CAMBIADA, user_id=user.id, actor_user_id=user.id
    )


def get_own_activity(db: Session, user: User) -> list[AuthAuditLog]:
    """Misma restricción que change_own_password: `user` viene siempre de
    get_current_user, así que esta lista nunca puede ampliarse a la
    actividad de otra cuenta manipulando la petición."""
    return repository.list_audit_entries_for_user(db, user.id)
