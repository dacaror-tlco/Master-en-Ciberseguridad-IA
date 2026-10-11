"""
Solo para desarrollo local: crea las tablas `cases` y `timeline_events`
(propiedad real de los Módulos 1 y 4, ver app/modules/shared/models.py)
y las puebla con un caso de ejemplo, para poder probar Módulo 5 de forma
aislada mientras esos módulos no existen todavía en `main`.

Deliberadamente NO usa Alembic: la migración de este módulo solo gestiona
`reports` (ver alembic/versions/0001_create_reports_table.py). Este script
se descarta en cuanto el proyecto se integre y esas tablas las cree de
verdad la migración de Módulo 1/4.

Uso: python scripts/seed_dev_db.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ver la nota de scripts/load_fixtures.py: sin esto `import app` falla al
# ejecutarlo como `python scripts/seed_dev_db.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.modules.shared.models import Case, EstadoCaso, TimelineEvent  # noqa: E402


def seed() -> None:
    Base.metadata.create_all(bind=engine, tables=[Case.__table__, TimelineEvent.__table__])

    db = SessionLocal()
    try:
        if db.query(Case).count() > 0:
            print("Ya hay datos de ejemplo, no se vuelve a sembrar.")
            return

        caso = Case(
            nombre="Intrusión servidor web - Cliente Acme",
            estado=EstadoCaso.EN_PROGRESO,
            fecha_creacion=datetime.now(timezone.utc) - timedelta(days=3),
            descripcion="Acceso no autorizado detectado en el servidor web de producción.",
            responsable="Ana Pérez",
        )
        db.add(caso)
        db.flush()

        base_time = datetime.now(timezone.utc) - timedelta(days=2)
        eventos = [
            ("evidences", 1, "Se recolecta imagen forense del disco del servidor.", 1),
            ("osint", 1, "IP de origen 203.0.113.10 marcada como maliciosa en VirusTotal.", 2),
            ("tracking", 1, "Detectado usuario 'www-data' ejecutando comandos inusuales.", 3),
        ]
        for i, (origen_modulo, origen_id, descripcion, orden) in enumerate(eventos):
            db.add(
                TimelineEvent(
                    id=f"tl-{i}",
                    case_id=caso.id,
                    fecha_hora=base_time + timedelta(hours=i),
                    descripcion=descripcion,
                    origen_modulo=origen_modulo,
                    origen_id=origen_id,
                    orden=orden,
                )
            )

        db.commit()
        print(f"Caso de ejemplo creado con id={caso.id} y {len(eventos)} eventos.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
