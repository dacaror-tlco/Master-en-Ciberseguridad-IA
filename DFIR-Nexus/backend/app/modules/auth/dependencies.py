"""
Dependencias FastAPI para proteger rutas de este backend (Casos). Este es
el fichero que, en la Fase 4, se duplica (no se importa) en OSINT/
Tracking/Timeline/Informes — cada uno con su propia copia mínima que
valida el mismo JWT/JWT_SECRET, sin importar código de este backend. Aquí
además se comprueba `activo` contra la tabla `users` porque este backend
es su dueño; los otros backends, al no poseer `users`, solo podrán
confiar en lo que dice el JWT en el momento de emitirlo (ver "fuera de
alcance": revocación inmediata).

401 (no autenticado: token ausente/inválido/expirado) vs. 403 (autenticado
pero sin permiso suficiente) — distinción exigida por el frontend (ver
propuesta de identidad, criterios de aceptación).
"""
import secrets

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth import repository
from app.modules.auth.models import Rol, User
from app.modules.auth.security import TokenExpiradoError, TokenInvalidoError, decodificar_token


def _extraer_token(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    return header.removeprefix("Bearer ").strip()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _extraer_token(request)
    try:
        payload = decodificar_token(token)
    except TokenExpiradoError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except TokenInvalidoError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = repository.get_by_id(db, int(payload["sub"]))
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inexistente o inactivo")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Los dos roles solo tienen una restricción real: admin es superestricto
    de analyst (ver propuesta de identidad, sección "roles"). No existe un
    `require_role("analyst")` separado — "requiere analyst" en la matriz de
    permisos significa en la práctica "cualquier usuario autenticado", que
    ya cubre get_current_user por sí solo.
    """
    if user.rol != Rol.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol admin")
    return user


def resolve_osint_actor(request: Request, db: Session = Depends(get_db)) -> str:
    """
    Dependencia EXCLUSIVA de POST /cases/{id}/auditoria/osint — no es una
    variante de get_current_user ni debe reutilizarse en ningún otro
    endpoint (ver propuesta de identidad y acceso, secciones 11-12). Dos
    señales independientes, cada una con su propio papel:

    1. `X-Service-Token`: prueba que la llamada viene de verdad del
       backend de OSINT, no de un cliente cualquiera con un JWT de
       usuario válido. Obligatoria — sin ella, o si no coincide (tiempo
       constante, ver secrets.compare_digest), 401. Un JWT de usuario
       válido SIN esta cabecera nunca basta para pasar por aquí.
    2. `Authorization: Bearer <jwt>`: el JWT del usuario que originó la
       operación en OSINT, reenviado tal cual por ese backend. Opcional
       de verdad — si falta, es inválido o ha caducado, NO se rechaza la
       llamada (el X-Service-Token ya la autentica por sí solo): se
       degrada a `actor="osint"`, nunca se pierde la entrada de
       auditoría por un detalle de identidad.
    """
    service_token = request.headers.get("X-Service-Token")
    if not service_token or not secrets.compare_digest(service_token, settings.OSINT_AUDIT_SERVICE_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Servicio no autorizado")

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return "osint"

    try:
        payload = decodificar_token(auth_header.removeprefix("Bearer ").strip())
    except (TokenExpiradoError, TokenInvalidoError):
        return "osint"

    user = repository.get_by_id(db, int(payload["sub"]))
    return user.nombre if user is not None else "osint"
