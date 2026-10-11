"""
Lógica de refresco de la timeline de un caso.

Auditoría Módulo 4 (2026-09-27):
- H-02: tras reconstruir la timeline se RELEE desde `timeline_events`
  antes de devolverla. Antes se devolvía la lista en memoria (dicts con
  `id = id de la fila origen`), lo que hacía que el `id` del response NO
  fuera el de `timeline_events`. El frontend usa ese id como key de
  React → colisiones entre fuentes cuyos ids coincidían numéricamente.
- H-03: un único commit al final; rollback ante cualquier excepción.
  Antes había dos commits separados (DELETE y luego INSERT) y una caída
  a mitad dejaba el caso sin timeline.
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.modules.timeline.repository import (
    delete_existing_timeline,
    get_evidence_events,
    get_osint_events,
    get_timeline_events,
    get_tracking_events,
    insert_timeline_events,
)


def refresh_timeline(db: Session, case_id: int) -> List[Dict[str, Any]]:
    """
    Reconstruye la timeline del caso desde las tres fuentes reales
    (tracking_events, evidences, osint_findings): snapshot completo —
    borra lo que hubiera y vuelve a insertar, en vez de intentar
    fusionar incrementalmente.
    """
    events: List[Dict[str, Any]] = []
    events.extend(get_tracking_events(db, case_id))
    events.extend(get_evidence_events(db, case_id))
    events.extend(get_osint_events(db, case_id))

    events.sort(key=lambda x: (x["fecha_hora"], x["origen_modulo"], x["origen_id"]))
    for idx, event in enumerate(events, start=1):
        event["orden"] = idx

    try:
        delete_existing_timeline(db, case_id)
        if events:
            insert_timeline_events(db, events)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # H-02: releer lo persistido para devolver los ids REALES de
    # timeline_events, no los de las filas origen.
    return get_timeline_events(db, case_id)
