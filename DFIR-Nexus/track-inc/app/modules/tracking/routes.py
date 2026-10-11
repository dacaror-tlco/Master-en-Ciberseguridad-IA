"""
Rutas FastAPI del Módulo 3 (Tracking post-incidente).

    POST /cases/{case_id}/tracking/analyze  -> sube un log, devuelve preview clasificado (NO persiste)
    POST /cases/{case_id}/tracking/events   -> persiste los eventos revisados/confirmados
    GET  /cases/{case_id}/tracking/events   -> lista los tracking_events ya guardados del caso
    GET  /cases/{case_id}/tracking/verify   -> verifica la integridad interna (capa opcional)
    GET  /cases-lookup                      -> casos para el selector del frontend

Consultar (listar, verificar) se permite en cualquier caso existente, también
eliminado; escribir (analizar para guardar, guardar) solo en un caso activo y
no archivado. Es el mismo criterio que aplica Casos.
"""

from __future__ import annotations

import hashlib
import os

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db

from . import service
from .chain_integrity import eventos_guardados_del_log
from .codificacion import decodificar_log
from .schemas import (
    AnalyzeLogResponse,
    CaseOption,
    SaveEventsRequest,
    SaveEventsResponse,
    TrackingEventOut,
    VerifyIntegrityResponse,
)

router = APIRouter(prefix="/cases/{case_id}/tracking", tags=["tracking"])

# Prefijo propio, fuera de /cases/{case_id}/tracking: es un selector para el
# frontend, no una ruta anidada bajo un caso concreto. No colisiona con el
# /cases del backend de Casos (proceso y puerto distintos), pero se nombra sin
# ambigüedad para dejar claro que Tracking no es dueño de esta información,
# solo la proyecta desde la tabla compartida. (Añadido por el equipo al
# integrar el módulo en `development`.)
lookup_router = APIRouter(tags=["tracking"])


@lookup_router.get("/cases-lookup", response_model=list[CaseOption])
def list_case_options(db: Session = Depends(get_db)) -> list[CaseOption]:
    return service.list_case_options(db)


def _max_bytes_log() -> int:
    """Tamaño máximo de un log subido (TRACKING_MAX_LOG_MB, 20 MB por defecto).

    20 MB es el mismo límite que aplica la pasarela nginx del despliegue
    (`client_max_body_size 20m`). Con un límite mayor aquí, un log de entre
    20 y 50 MB recibía el 413 en HTML de nginx en vez del error JSON de la API.
    """
    return int(float(os.environ.get("TRACKING_MAX_LOG_MB", "20")) * 1024 * 1024)


def _analizar(db: Session, case_id: int, contenido: bytes, nombre: str, zona_horaria: str) -> AnalyzeLogResponse:
    # Analizar no escribe, pero su único fin es guardar: se avisa ya de que
    # el caso no admite eventos, en vez de al pulsar "Guardar".
    service.exigir_caso_modificable(db, case_id)
    text, codificacion = decodificar_log(contenido)
    respuesta = service.analyze_log_content(text, fuente_log=nombre, zona_horaria=zona_horaria)
    respuesta.codificacion = codificacion
    respuesta.sha256_log = hashlib.sha256(contenido).hexdigest()
    respuesta.eventos_ya_guardados = eventos_guardados_del_log(case_id, respuesta.sha256_log)
    return respuesta


@router.post(
    "/analyze",
    response_model=AnalyzeLogResponse,
    # Los campos opcionales vacíos (salida, comando decodificado, usuario...)
    # no viajan: en un log grande eran más de 1 MB de "null".
    response_model_exclude_none=True,
    responses={
        404: {"description": "Caso inexistente"},
        409: {"description": "Caso eliminado o archivado: no admite eventos"},
        413: {"description": "Fichero demasiado grande"},
    },
)
async def analyze_log(
    case_id: int,
    file: UploadFile,
    zona_horaria: str = Form(
        "UTC",
        description="Zona horaria en que están escritas las horas del log: 'UTC' o un desplazamiento como '+02:00'.",
    ),
    db: Session = Depends(get_db),
) -> AnalyzeLogResponse:
    limite = _max_bytes_log()
    contenido = await file.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(status_code=413, detail=f"El fichero supera el máximo de {limite // (1024 * 1024)} MB.")
    try:
        # El análisis es CPU puro (segundos en un log grande). Ejecutarlo aquí,
        # dentro del bucle de eventos, bloqueaba la aplicación ENTERA mientras
        # duraba: ni Casos ni ninguna otra petición respondía.
        return await run_in_threadpool(
            _analizar, db, case_id, contenido, file.filename or "log_subido.txt", zona_horaria
        )
    except service.CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except service.CasoNoModificableError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:  # FicheroNoTextoError o zona horaria no válida
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/events",
    response_model=SaveEventsResponse,
    responses={409: {"description": "Caso eliminado o archivado, o ese fichero de log ya se guardó en el caso"}},
)
def save_events(case_id: int, payload: SaveEventsRequest, db: Session = Depends(get_db)) -> SaveEventsResponse:
    if payload.case_id != case_id:
        raise HTTPException(status_code=400, detail="case_id de la URL y del cuerpo no coinciden.")
    try:
        return service.save_events(db, payload)
    except service.CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (service.CasoNoModificableError, service.LogYaGuardadoError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/events", response_model=list[TrackingEventOut])
def list_events(
    case_id: int,
    # Mismo patrón de paginación que Casos y OSINT. Un log grande puede dejar
    # miles de eventos en un caso; antes se devolvían todos de una vez.
    skip: int = Query(0, ge=0, description="Eventos a saltar."),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de eventos a devolver."),
    db: Session = Depends(get_db),
) -> list[TrackingEventOut]:
    try:
        return service.get_events_for_case(db, case_id, skip, limit)
    except service.CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/verify", response_model=VerifyIntegrityResponse)
def verify_integrity(case_id: int, db: Session = Depends(get_db)) -> VerifyIntegrityResponse:
    try:
        return service.verify_integrity(db, case_id)
    except service.CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
