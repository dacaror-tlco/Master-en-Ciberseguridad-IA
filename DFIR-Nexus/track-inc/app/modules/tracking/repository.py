"""
Acceso a datos de `tracking_events`. Sin lógica de negocio — eso vive en
service.py. Sigue el patrón repository.py que pide CLAUDE.md.

`cases` no es de este módulo (es del Módulo 1): se lee con SQL directo y
mínimo, sin importar ningún modelo de Casos — un backend no importa modelos
Python de otro (docs/CONTRATOS.md del repositorio común).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .models import TrackingEvent

_columnas_cases: dict[str, set[str]] = {}


@dataclass(frozen=True)
class EstadoCaso:
    """Lo que Tracking necesita saber de un caso para decidir qué permite."""

    existe: bool
    eliminado: bool = False
    estado: str | None = None


def _columnas_de_cases(db: Session) -> set[str]:
    """Columnas reales de `cases`. El Módulo 1 añade `eliminado` (borrado
    lógico); la tabla de pruebas local puede no tenerla. Se mira la base de
    datos, no un modelo: Tracking no tiene modelo de `cases`."""
    clave = str(db.get_bind().url)
    if clave not in _columnas_cases:
        _columnas_cases[clave] = {c["name"] for c in inspect(db.get_bind()).get_columns("cases")}
    return _columnas_cases[clave]


def estado_caso(db: Session, case_id: int) -> EstadoCaso:
    tiene_eliminado = "eliminado" in _columnas_de_cases(db)
    columnas = "estado, eliminado" if tiene_eliminado else "estado"
    fila = db.execute(text(f"SELECT {columnas} FROM cases WHERE id = :id"), {"id": case_id}).first()
    if fila is None:
        return EstadoCaso(existe=False)
    return EstadoCaso(
        existe=True,
        eliminado=bool(fila[1]) if tiene_eliminado else False,
        estado=getattr(fila[0], "value", fila[0]),
    )


def list_case_options(db: Session) -> list[dict]:
    """Para el selector de caso del frontend: solo las tres columnas que hacen
    falta, y sin los casos eliminados (igual que el listado de Casos, que los
    oculta por defecto)."""
    filtro = "WHERE eliminado = 0 " if "eliminado" in _columnas_de_cases(db) else ""
    filas = db.execute(text(f"SELECT id, nombre, estado FROM cases {filtro}ORDER BY id DESC")).mappings().all()
    return [{**f, "estado": getattr(f["estado"], "value", f["estado"])} for f in filas]


def create_tracking_events(db: Session, filas: list[dict[str, Any]]) -> list[TrackingEvent]:
    """Inserta todas las filas en un solo flush (ids asignados, sin commit).

    Antes era un flush por fila, más un refresh por fila tras el commit: dos
    viajes a la base de datos por evento, que contra un MySQL remoto
    convertían guardar un log grande en minutos.
    """
    rows = [TrackingEvent(**fila) for fila in filas]
    db.add_all(rows)
    db.flush()
    return rows


def list_by_case(db: Session, case_id: int, skip: int = 0, limit: int | None = None) -> list[TrackingEvent]:
    # `id` desempata eventos del mismo segundo: sin él, su orden relativo
    # quedaba a criterio del motor y podía variar entre consultas.
    stmt = (
        select(TrackingEvent)
        .where(TrackingEvent.case_id == case_id)
        .order_by(TrackingEvent.hora.asc(), TrackingEvent.id.asc())
    )
    # Paginación con el mismo patrón que Casos y OSINT (skip/limit). `limit`
    # a None es para uso interno (verificar la integridad necesita TODAS las
    # filas del caso, no una página).
    if skip:
        stmt = stmt.offset(skip)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, event_id: int) -> TrackingEvent | None:
    return db.get(TrackingEvent, event_id)
