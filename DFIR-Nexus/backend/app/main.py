import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.modules.auth.routes import router as auth_router
from app.modules.cases.routes import router as cases_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Nexus", description="Plataforma de asistencia pericial informática")


@app.middleware("http")
async def convertir_errores_no_controlados(request: Request, call_next):
    """
    Sin esto, una excepción no controlada (p. ej. no poder conectar con
    MySQL) se propaga como un 500 "en bruto" de Starlette que **no pasa
    por CORSMiddleware** — el navegador nunca ve la cabecera
    Access-Control-Allow-Origin y lo reporta como un bloqueo de CORS,
    aunque la configuración de CORS sea correcta (verificado: un
    `@app.exception_handler(Exception)` normal NO basta para esto en esta
    versión de FastAPI/Starlette — su respuesta tampoco atraviesa
    CORSMiddleware; solo un middleware HTTP que envuelve `call_next()` sí
    lo hace, porque su respuesta es un Response ASGI normal que sale por
    el mismo camino que una respuesta correcta).

    No cambia ninguna lógica de negocio: solo asegura que cualquier error,
    incluido uno inesperado, se sirve como una respuesta normal que sí
    lleva las cabeceras CORS — así el frontend ve un 500 real y no un
    falso positivo de CORS que oculta el problema de verdad.
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# Convención del proyecto (ver docs/INTEGRACION_Y_DESPLIEGUE.md): el
# frontend se abre siempre en http://localhost:5173, nunca en
# http://127.0.0.1:5173 — son orígenes distintos para CORS aunque
# resuelvan a la misma máquina, y solo el primero está en esta lista.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cases_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
