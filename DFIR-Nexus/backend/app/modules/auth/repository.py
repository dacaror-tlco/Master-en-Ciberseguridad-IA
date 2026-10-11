from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.auth.models import AuthAuditLog, AuthEvento, Rol, User
from app.modules.auth.schemas import UserCreate


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def create_user(db: Session, data: UserCreate, password_hash: str) -> User:
    user = User(nombre=data.nombre, email=data.email, password_hash=password_hash, rol=data.rol)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def apply_update(db: Session, user: User, campos: dict) -> User:
    for field, value in campos.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def registrar_ultimo_login(db: Session, user: User) -> None:
    user.ultimo_login = _now()
    db.commit()


def count_admins_activos(db: Session, excluir_id: int | None = None) -> int:
    query = db.query(User).filter(User.rol == Rol.ADMIN, User.activo.is_(True))
    if excluir_id is not None:
        query = query.filter(User.id != excluir_id)
    return query.count()


def list_audit_entries_for_user(db: Session, user_id: int, limit: int = 50) -> list[AuthAuditLog]:
    """Actividad propia de la pantalla de Perfil: SIEMPRE filtrada por
    user_id (el sujeto del evento), nunca por un id que decida el
    llamador — el único id que entra aquí es el que ya resolvió
    get_current_user a partir del JWT. Mismo orden que
    list_audit_log (case_audit_log): más reciente primero."""
    return (
        db.query(AuthAuditLog)
        .filter(AuthAuditLog.user_id == user_id)
        .order_by(AuthAuditLog.creado_en.desc(), AuthAuditLog.id.desc())
        .limit(limit)
        .all()
    )


def add_audit_entry(
    db: Session,
    *,
    evento: AuthEvento,
    user_id: int | None,
    actor_user_id: int | None,
    detalle: dict | None = None,
) -> AuthAuditLog:
    entry = AuthAuditLog(evento=evento, user_id=user_id, actor_user_id=actor_user_id, detalle=detalle)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
