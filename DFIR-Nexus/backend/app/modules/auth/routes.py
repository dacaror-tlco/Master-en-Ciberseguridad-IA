from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AuthAuditEntry,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.auth.service import (
    AutoDesactivacionError,
    CurrentPasswordIncorrectError,
    EmailYaRegistradoError,
    InvalidCredentialsError,
    PasswordConfirmationMismatchError,
    PasswordTooShortError,
    UltimoAdminError,
    UserNotFoundError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        token, expires_in, _user = service.authenticate(db, data)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    return LoginResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Cambia la contraseña del usuario autenticado — nunca la de otro: el
    usuario objetivo es siempre `current_user` (resuelto por
    get_current_user a partir del `sub` del JWT), no hay ningún `user_id`
    en el body que un cliente pueda manipular para apuntar a otra cuenta.
    """
    try:
        service.change_own_password(db, current_user, data)
    except CurrentPasswordIncorrectError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual incorrecta"
        )
    except PasswordConfirmationMismatchError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La confirmación no coincide con la nueva contraseña",
        )
    except PasswordTooShortError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La nueva contraseña debe tener al menos {service.LONGITUD_MINIMA_PASSWORD} caracteres",
        )


@router.get("/me/actividad", response_model=list[AuthAuditEntry])
def my_activity(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[AuthAuditEntry]:
    """Actividad de auth_audit_log del propio usuario — filtrada siempre
    por el id que resolvió get_current_user, nunca por uno que decida el
    llamador (no hay parámetro de user_id en esta ruta)."""
    return service.get_own_activity(db, current_user)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> UserRead:
    try:
        return service.create_user(db, data, actor=admin)
    except EmailYaRegistradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> list[UserRead]:
    return service.list_users(db)


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserRead:
    try:
        return service.update_user(db, user_id, data, actor=admin)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    except AutoDesactivacionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="No puedes desactivar tu propia cuenta"
        )
    except UltimoAdminError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esto dejaría el sistema sin ningún administrador activo",
        )
