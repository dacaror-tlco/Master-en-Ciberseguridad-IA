"""
Acceso a datos de Timeline. `timeline_events` es propia (se lee/escribe
con SQL directo, igual que en el resto de este backend, por simetría con
las lecturas de tablas ajenas). `tracking_events`, `evidences` y
`osint_findings` son de otros backends: se leen con SQL mínimo y
explícito, nunca importando sus modelos Python (ver docs/CONTRATOS.md).

Importante sobre `osint_findings`: el filtro `case_id = :case_id` ya es
exacto (case_id explícito, columna nullable) — no hay heurística de
ningún tipo aquí (ni por subject_value, ni por dominio, ni por nombre).
Si `case_id` está a NULL en scam-shield porque el análisis no se asoció
a un caso, esa fila simplemente no aparece en la timeline de nadie hasta
que OSINT la asocie explícitamente.

Auditoría Módulo 4 (2026-09-27):
- H-03: `delete_existing_timeline` e `insert_timeline_events` YA NO
  commitean. El commit lo hace el servicio al final, en una única
  transacción; si algo falla entre el DELETE y el INSERT, el rollback
  del servicio deja la tabla como estaba (antes se podía quedar sin
  timeline si el proceso moría entre los dos commits).
- H-07: `insert_timeline_events` usa executemany (lista de dicts a
  `execute`) en vez de N INSERTs en bucle.
"""

from typing import Any, Dict, List

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def table_exists(db: Session, table_name: str) -> bool:
    inspector = inspect(db.bind)
    return table_name in inspector.get_table_names()


def get_timeline_events(db: Session, case_id: int) -> List[Dict[str, Any]]:
    query = text("""
        SELECT id, case_id, fecha_hora, descripcion, origen_modulo, origen_id, orden
        FROM timeline_events
        WHERE case_id = :case_id
        ORDER BY orden
    """)
    result = db.execute(query, {"case_id": case_id}).fetchall()
    return [dict(row._mapping) for row in result]


def get_tracking_events(db: Session, case_id: int) -> List[Dict[str, Any]]:
    if not table_exists(db, "tracking_events"):
        return []
    query = text("""
        SELECT id, case_id, hora as fecha_hora, evento as descripcion, 'tracking' as origen_modulo, id as origen_id
        FROM tracking_events
        WHERE case_id = :case_id
    """)
    result = db.execute(query, {"case_id": case_id}).fetchall()
    return [dict(row._mapping) for row in result]


def get_evidence_events(db: Session, case_id: int) -> List[Dict[str, Any]]:
    """
    `COALESCE(fecha_adquisicion, fecha_subida)`: usa el timestamp forense
    real (cuándo ocurrió/se adquirió la evidencia) cuando el Módulo 1 lo
    conoce, y solo si no lo tiene cae en fecha_subida (alta administrativa
    del registro) — evita mezclar ambos conceptos en la cronología (ver
    Módulo 1, backend/app/modules/cases/models.py).

    `eliminado`/`fecha_adquisicion` son columnas añadidas por el Módulo 1
    después de la integración original; si no existen (base más antigua
    sin esas migraciones aplicadas todavía) se degrada sin romperse en vez
    de fallar con "Unknown column".
    """
    if not table_exists(db, "evidences"):
        return []
    columnas = {c["name"] for c in inspect(db.bind).get_columns("evidences")}
    fecha_hora_expr = (
        "COALESCE(fecha_adquisicion, fecha_subida)" if "fecha_adquisicion" in columnas else "fecha_subida"
    )
    filtro_eliminado = "AND (eliminado = 0 OR eliminado IS NULL)" if "eliminado" in columnas else ""
    query = text(f"""
        SELECT id, case_id, {fecha_hora_expr} as fecha_hora, CONCAT(tipo, ': ', valor) as descripcion, 'evidence' as origen_modulo, id as origen_id
        FROM evidences
        WHERE case_id = :case_id
        {filtro_eliminado}
    """)
    result = db.execute(query, {"case_id": case_id}).fetchall()
    return [dict(row._mapping) for row in result]


def get_osint_events(db: Session, case_id: int) -> List[Dict[str, Any]]:
    if not table_exists(db, "osint_findings"):
        return []
    query = text("""
        SELECT id, case_id, analyzed_at as fecha_hora, headline as descripcion, 'osint' as origen_modulo, id as origen_id
        FROM osint_findings
        WHERE case_id = :case_id
    """)
    result = db.execute(query, {"case_id": case_id}).fetchall()
    return [dict(row._mapping) for row in result]


def delete_existing_timeline(db: Session, case_id: int) -> None:
    """Borra la timeline del caso SIN commitear — el commit lo hace el
    servicio al cerrar la transacción completa (H-03)."""
    db.execute(
        text("DELETE FROM timeline_events WHERE case_id = :case_id"),
        {"case_id": case_id},
    )


def insert_timeline_events(db: Session, events: List[Dict[str, Any]]) -> None:
    """Inserta en bloque con executemany, SIN commitear (H-03/H-07)."""
    if not events:
        return
    payload = [
        {
            "case_id": e["case_id"],
            "fecha_hora": e["fecha_hora"],
            "descripcion": e["descripcion"],
            "origen_modulo": e["origen_modulo"],
            "origen_id": e["origen_id"],
            "orden": e["orden"],
        }
        for e in events
    ]
    db.execute(
        text("""
            INSERT INTO timeline_events
                (case_id, fecha_hora, descripcion, origen_modulo, origen_id, orden)
            VALUES
                (:case_id, :fecha_hora, :descripcion, :origen_modulo, :origen_id, :orden)
        """),
        payload,
    )
