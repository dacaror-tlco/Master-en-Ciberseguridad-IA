"""
Casos de prueba para trabajar con el módulo EN LOCAL, sin el backend de Casos.

En `development`, `cases` es del Módulo 1: Tracking no la define, no importa
su modelo y no expone ninguna ruta para crear casos (el placeholder que había
aquí se retiró al integrar; ver docs/CONTRATOS.md del repositorio común). Pero
trabajando el módulo por separado, contra la SQLite local, hace falta poder
crear algún caso para probarlo.

Por eso este router:

  - Solo se monta si la base de datos es SQLite (ver app/main.py). Contra
    MySQL —la base compartida de Aiven o la del despliegue— no existe: ahí
    los casos los crea Casos.
  - Lee y escribe la tabla `cases` con SQL mínimo, igual que el resto de
    Tracking, sin modelo ORM propio (la crea la migración 0001 en local).

Mantiene las rutas del antiguo placeholder (`GET /cases/`, `POST /cases/`),
que son las que usa el frontend de pruebas de este repositorio.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/cases", tags=["casos locales (solo SQLite)"])


@router.post("/", status_code=201)
def crear_caso_local(
    nombre: str = Query(..., min_length=1, max_length=150),
    responsable: str = Query(..., min_length=1, max_length=100),
    descripcion: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    resultado = db.execute(
        text(
            "INSERT INTO cases (nombre, responsable, descripcion, estado) "
            "VALUES (:nombre, :responsable, :descripcion, 'abierto')"
        ),
        {"nombre": nombre, "responsable": responsable, "descripcion": descripcion},
    )
    db.commit()
    return {"id": resultado.lastrowid, "nombre": nombre, "estado": "abierto", "responsable": responsable}


@router.get("/")
def listar_casos_locales(db: Session = Depends(get_db)) -> list[dict]:
    filas = db.execute(text("SELECT id, nombre, estado FROM cases ORDER BY id DESC")).mappings().all()
    return [dict(f) for f in filas]
