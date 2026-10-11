"""
Punto de entrada de Timeline (Módulo 4), backend independiente.

En `feature/timeline-integration` este módulo vivía dentro del proceso de
Casos (dos líneas añadidas a su main.py). Al integrarlo en `development`
se separa a su propio proceso/puerto, igual que OSINT y Tracking (ver
docs/CONTRATOS.md) — Timeline no debe compartir código ni proceso con
Casos, aunque comparta la base de datos.

Arrancar con:
    uvicorn app.main:app --reload --port 8002
"""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.modules.auth.dependencies import get_current_user
from app.modules.timeline.routes import router as timeline_router

app = FastAPI(
    title="Nexus — Módulo 4 (Timeline)",
    description="Construye y persiste la línea temporal de un caso a partir de tracking_events, evidences y osint_findings.",
    version="1.0",
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def convertir_errores_no_controlados(request: Request, call_next):
    """Ver docs/INTEGRACION_Y_DESPLIEGUE.md: evita que un 500 no controlado
    (p. ej. fallo de conexión a MySQL al leer tracking_events/evidences/
    osint_findings) se reporte al navegador como un falso bloqueo de CORS."""
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# Fase final (hardening): el frontend oficial ya está desplegado — se
# acota al único origen desde el que corre en desarrollo (mismo valor
# que Casos). En producción no hace falta tocar esto: el navegador solo
# habla con el origen del gateway (ver deploy/gateway/nginx.conf), nunca
# directamente con este backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fase 4: sus 2 endpoints quedan autenticados, sin excepciones —
# dependencia a nivel de router, sin tocar
# app/modules/timeline/routes.py.
app.include_router(timeline_router, dependencies=[Depends(get_current_user)])


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
