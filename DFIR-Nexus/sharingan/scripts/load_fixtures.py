"""
Carga un fichero de fixture (JSON) que simula lo que producirían los
Módulos 1 (caso) y 4 (timeline ya correlacionado) contra la base de datos
configurada en DATABASE_URL. Solo para desarrollo/pruebas manuales de
Módulo 5 — ver fixtures/*.json para el formato esperado y
app/modules/shared/models.py para por qué este módulo mantiene su propia
copia de estas tablas mientras Módulo 1/4 no existen todavía.

Uso:
    python scripts/load_fixtures.py fixtures/caso_001_intrusion_web.json

Imprime el `case_id` resultante, que es el que se usa luego contra
POST /reports/generate.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Python pone en sys.path el directorio del script (scripts/), no el actual,
# así que sin esto `import app` falla al invocarlo como dice el README:
#   python scripts/load_fixtures.py fixtures/caso_001_intrusion_web.json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.modules.shared.models import (  # noqa: E402
    Case,
    EstadoCaso,
    Evidence,
    OsintResult,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)

_TABLAS_SIMULADAS = [
    Case.__table__,
    Evidence.__table__,
    OsintResult.__table__,
    TrackingEvent.__table__,
    TimelineEvent.__table__,
]


def construir_objetos(data: dict) -> tuple[Case, dict[str, list]]:
    """
    Convierte el JSON en instancias del modelo **sin persistirlas**.

    Se separa de la carga en base de datos para que
    `scripts/previsualizar_informe.py` pueda componer un informe con la misma
    fixture sin necesitar MySQL: el mapeo JSON → objeto es idéntico, así que
    lo que se previsualiza es exactamente lo que se generaría contra la BD.
    """
    caso_data = data["case"]
    caso = Case(
        nombre=caso_data["nombre"],
        estado=EstadoCaso(caso_data["estado"]),
        fecha_creacion=datetime.fromisoformat(caso_data["fecha_creacion"]),
        descripcion=caso_data.get("descripcion"),
        responsable=caso_data.get("responsable"),
    )

    hijos = {
        "evidences": [
            Evidence(
                tipo=e["tipo"],
                valor=e["valor"],
                fecha_subida=datetime.fromisoformat(e["fecha_subida"]),
                observaciones=e.get("observaciones"),
            )
            for e in data.get("evidences", [])
        ],
        "osint_results": [
            OsintResult(
                tipo_indicador=o["tipo_indicador"],
                valor=o["valor"],
                reputacion=o.get("reputacion"),
                pais=o.get("pais"),
                detecciones=o.get("detecciones"),
                fuente=o["fuente"],
                fecha_consulta=datetime.fromisoformat(o["fecha_consulta"]),
                raw_response=o.get("raw_response"),
            )
            for o in data.get("osint_results", [])
        ],
        "tracking_events": [
            TrackingEvent(
                # Los Modulos 3 y 4 generan sus propios identificadores (el
                # Modulo 3 propone `evt-7f3a9c2e`), asi que la fixture puede
                # traerlos. Si no vienen se numeran, solo para desarrollo.
                #
                # El numero **a secas**, no `evt-{indice}`: `tracking_events.id`
                # no es autoincremental —es texto, lo fija el Modulo 3— asi que
                # este valor es el que acaba en la columna «Id» del Anexo C. Las
                # fixtures que no traen id referencian sus eventos como
                # `origen_id: 1`, igual que hacen con evidencias y OSINT, de modo
                # que prefijarlo dejaba la cronologia citando «tracking#1» contra
                # un anexo que decia «evt-1»: dos tablas del mismo informe
                # nombrando distinto el mismo registro, que es justo lo que la
                # columna «Ref.» existe para impedir.
                id=t.get("id", str(indice)),
                hora=datetime.fromisoformat(t["hora"]),
                evento=t["evento"],
                severidad=Severidad(t["severidad"]),
                fuente_log=t.get("fuente_log"),
                usuario_detectado=t.get("usuario_detectado"),
            )
            for indice, t in enumerate(data.get("tracking_events", []), start=1)
        ],
        "timeline_events": [
            TimelineEvent(
                id=ev.get("id", f"tl-{indice}"),
                fecha_hora=datetime.fromisoformat(ev["fecha_hora"]),
                descripcion=ev["descripcion"],
                origen_modulo=ev["origen_modulo"],
                origen_id=ev["origen_id"],
                orden=ev["orden"],
            )
            for indice, ev in enumerate(data.get("timeline_events", []), start=1)
        ],
    }
    return caso, hijos


def load_fixture(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    caso, hijos = construir_objetos(data)

    Base.metadata.create_all(bind=engine, tables=_TABLAS_SIMULADAS)

    db = SessionLocal()
    try:
        db.add(caso)
        db.flush()  # asigna el id del caso, necesario para las filas hijas

        for filas in hijos.values():
            for fila in filas:
                fila.case_id = caso.id
                db.add(fila)

        db.commit()
        db.refresh(caso)
        return caso.id
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Ruta al fichero JSON de fixture")
    args = parser.parse_args()

    case_id = load_fixture(args.fixture)
    print(f"Caso creado con case_id={case_id} a partir de {args.fixture.name}")
