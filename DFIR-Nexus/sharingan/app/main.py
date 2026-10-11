import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.chat.routes import router as chat_router
from app.modules.reports.routes import cases_router, router as reports_router

app = FastAPI(
    title=settings.app_name,
    description="Módulo 5 de DFIR Nexus: generación de informes periciales asistida por IA.",
    version="0.1.0",
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def convertir_errores_no_controlados(request: Request, call_next):
    """
    Ver docs/INTEGRACION_Y_DESPLIEGUE.md. Tiene que registrarse ANTES que
    CORSMiddleware (más abajo) para quedar dentro de él en la pila real
    de middlewares — Starlette anida en orden inverso al de registro, así
    que lo último añadido queda más "por fuera". Si se registrara después
    de CORSMiddleware, su respuesta ante un error no llevaría cabeceras
    CORS (comprobado empíricamente durante esta integración).
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cabeceras_de_seguridad(request, call_next):
    """
    `nosniff` es la que importa aquí: sin ella, un navegador puede decidir por
    su cuenta que una respuesta JSON o un PDF «parece» HTML y renderizarlo. Un
    informe contiene texto que viene de los módulos de OSINT y tracking, o sea
    contenido que un atacante puede haber influido, así que la respuesta tiene
    que interpretarse exactamente con el tipo que declara y no con el que el
    navegador adivine.

    La política de contenido del HTML del informe no se pone aquí, sino en su
    propia respuesta (ver `routes.download_report`): una política estricta
    global rompería la interfaz de `/docs`.
    """
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    return respuesta

# El esquema se gestiona con Alembic (ver alembic/), no con create_all():
# `reports` se crea con su migración; `cases`/`timeline_events` los poseen
# los Módulos 1 y 4 (en desarrollo local, ver scripts/seed_dev_db.py).

# Fase 4: los 5 endpoints de este backend quedan autenticados, sin
# excepciones — dependencia a nivel de router, sin tocar
# app/modules/reports/routes.py.
_auth = [Depends(get_current_user)]
app.include_router(reports_router, dependencies=_auth)
# `cases_router` (prefix "/cases") expone una única ruta de solo lectura,
# GET /cases/{case_id}/reports — no es una reivindicación de propiedad
# sobre /cases: Informes es un backend independiente en su propio proceso
# y puerto (ver docs/CONTRATOS.md, Fase 4), así que no colisiona con el
# /cases real de Casos aunque comparta el nombre del recurso. Mismo patrón
# ya usado por Tracking (/cases/{case_id}/tracking/...).
app.include_router(cases_router, dependencies=_auth)
# Asistente conversacional (POST /chat, POST /chat/stream). Vive en este
# backend porque es exactamente la lectura que ya hace Informes —las seis
# tablas del contrato, en solo lectura— con el mismo cliente de Anthropic
# ya configurado; montarlo como sexto proceso habría duplicado venv,
# .env, puerto y espejo de modelos sin ganar aislamiento real. No escribe
# nada ni añade tablas: ver app/modules/chat/schemas.py.
#
# Autenticado con la misma dependencia de router que el resto, y aquí
# importa más que en ninguna otra ruta: al asistente se le pasa el
# expediente entero de un caso en el prompt —evidencias, usuarios, IPs,
# rutas—, así que un `/chat` abierto sería una lectura completa de
# cualquier investigación sin credenciales. El aislamiento por caso que
# aplica el servicio impide saltar de un caso a otro, no entrar sin ser
# nadie.
app.include_router(chat_router, dependencies=_auth)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
