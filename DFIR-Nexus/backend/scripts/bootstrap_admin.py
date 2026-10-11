"""
Crea el primer usuario admin de Nexus. Deliberadamente NO existe ninguna
contraseña fija insertada por una migración: la contraseña la da quien
ejecuta este script, por variable de entorno o de forma interactiva.

Uso (desde backend/, con el entorno virtual activado y las variables de
MYSQL_* ya resueltas, igual que para `alembic upgrade head`):

    python -m scripts.bootstrap_admin

Con variables de entorno (útil en despliegue no interactivo, p. ej. el
Dockerfile de producción):

    ADMIN_EMAIL=admin@nexus.local ADMIN_PASSWORD=... python -m scripts.bootstrap_admin

Si faltan, se piden por terminal (la contraseña con getpass, nunca se
muestra en pantalla ni queda en el historial de la shell).

Es idempotente por construcción: si ya existe CUALQUIER admin activo, el
script se niega a crear uno nuevo y no hace nada — evita duplicar
"primeros admins" por un re-run accidental. Para cambiar la contraseña de
un admin ya existente, usar PUT /auth/users/{id} autenticado como ese
mismo admin (o como otro admin), nunca este script.
"""
import getpass
import os
import sys

from app.core.database import SessionLocal
from app.modules.auth import repository
from app.modules.auth.models import Rol
from app.modules.auth.schemas import UserCreate
from app.modules.auth.security import hash_password


def main() -> int:
    db = SessionLocal()
    try:
        if repository.count_admins_activos(db) > 0:
            print("Ya existe al menos un administrador activo. No se crea ninguno nuevo.")
            return 1

        email = os.environ.get("ADMIN_EMAIL") or input("Email del admin: ").strip()
        nombre = os.environ.get("ADMIN_NOMBRE") or input("Nombre: ").strip()
        password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Contraseña: ")
        confirmacion = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Repite la contraseña: ")

        if password != confirmacion:
            print("Las contraseñas no coinciden.", file=sys.stderr)
            return 1
        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres.", file=sys.stderr)
            return 1
        if repository.get_by_email(db, email) is not None:
            print(f"Ya existe un usuario con el email {email!r}.", file=sys.stderr)
            return 1

        data = UserCreate(nombre=nombre, email=email, password=password, rol=Rol.ADMIN)
        user = repository.create_user(db, data, hash_password(password))
        print(f"Admin creado: id={user.id} email={user.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
