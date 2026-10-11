"""
Punto de entrada de la app FastAPI de Nexus (backend).

Arrancar con:
    uvicorn app.main:app --reload --port 8000

Documentación interactiva automática en /docs
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from sqlalchemy.engine import make_url

from app.modules.auth.dependencies import autenticacion_desactivada, get_current_user
from app.modules.auth.security import SECRETO_POR_DEFECTO, JWT_SECRET
from app.modules.tracking.routes import lookup_router as tracking_lookup_router
from app.modules.tracking.routes import router as tracking_router
from app.core.database import Base, DATABASE_URL, engine

logger = logging.getLogger(__name__)


def _verificar_esquema() -> None:
    """Comprueba que las tablas existen antes de aceptar peticiones.

    Aquí había un `Base.metadata.create_all()`. Se retiró porque creaba
    el esquema saltándose Alembic: la base de datos quedaba sin tabla
    `alembic_version` y divergía en silencio de la del resto del equipo,
    contradiciendo la regla de CLAUDE.md de que ningún cambio del modelo
    se aplica sin su migración. El fallo aparecía mucho más tarde, al
    intentar migrar sobre un esquema que Alembic creía inexistente.

    Ahora se falla al arrancar y con instrucciones, en vez de dar un
    "no such table" críptico en la primera petición.
    """
    faltan = sorted(set(Base.metadata.tables) - set(inspect(engine).get_table_names()))
    if faltan:
        raise RuntimeError(
            f"Faltan tablas en la base de datos: {', '.join(faltan)}.\n"
            "El esquema lo gestiona Alembic. Ejecuta desde la raíz del repositorio:\n"
            "    alembic upgrade head"
        )


def _avisar_del_estado_de_la_autenticacion() -> None:
    """Deja en el log, al arrancar, si los endpoints están protegidos.

    Las dos situaciones que pueden pasar desapercibidas y que conviene ver
    escritas: que alguien haya arrancado con la autenticación desactivada
    fuera de su sitio (el módulo suelto), y que el secreto siga siendo el
    de ejemplo, con el que cualquiera puede firmarse un token válido.
    """
    log = logging.getLogger("uvicorn.error")
    if autenticacion_desactivada():
        log.warning(
            "AUTENTICACION DESACTIVADA (TRACKING_AUTH_DESACTIVADA): los endpoints "
            "responden sin token. Solo para ejecutar este módulo suelto."
        )
    elif JWT_SECRET == SECRETO_POR_DEFECTO:
        log.warning(
            "JWT_SECRET sigue siendo el valor de ejemplo (%r): cualquiera puede "
            "firmar un token válido. Debe ser el mismo secreto que emite Casos.",
            SECRETO_POR_DEFECTO,
        )
    else:
        log.info("Autenticación: obligatoria (JWT verificado con el secreto de Casos)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se anuncia a qué base se conecta (sin contraseña). Con un `.env`
    # apuntando a la base COMPARTIDA, basta con arrancar sin DATABASE_URL para
    # escribir en la del equipo; este aviso lo hace visible desde el principio.
    logging.getLogger("uvicorn.error").info(
        "Base de datos: %s", make_url(DATABASE_URL).render_as_string(hide_password=True)
    )
    _avisar_del_estado_de_la_autenticacion()
    _verificar_esquema()
    yield


app = FastAPI(
    title="Nexus — Módulo 3 (Tracking Post-Incidente)",
    description="Análisis de logs post-incidente: clasificación de eventos y persistencia en tracking_events.",
    version="1.0",
    lifespan=lifespan,
)

def _origenes_cors() -> list[str]:
    """Orígenes que pueden llamar a la API desde OTRO origen.

    La aplicación normal no lo necesita: el backend sirve el frontend y todo
    va al mismo origen. Solo el modo desarrollo (Vite en :5173) es otro
    origen. Antes se permitía cualquiera (`*`): cualquier web abierta en el
    navegador del perito podía escribir en `tracking_events` a través de su
    backend local, y con el `.env` apuntando a la base compartida, en la del
    equipo. `CORS_ORIGINS` (separados por comas) amplía la lista si hace falta.
    """
    extra = os.environ.get("CORS_ORIGINS", "")
    return ["http://localhost:5173", "http://127.0.0.1:5173"] + [
        o.strip() for o in extra.split(",") if o.strip()
    ]


@app.middleware("http")
async def convertir_errores_no_controlados(request: Request, call_next):
    """
    Igual que en el resto de backends de Nexus (ver
    docs/INTEGRACION_Y_DESPLIEGUE.md del repositorio común): un 500 no
    controlado se sirve como respuesta normal, con cabeceras CORS, en vez de
    como un 500 "en bruto" que el navegador reporta como bloqueo de CORS.
    (Añadido por el equipo al integrar el módulo en `development`.) No cubre
    el fallo de conexión a MySQL en el arranque: ese impide que el proceso
    llegue a aceptar peticiones.
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# Compresión de respuestas: el análisis de un log grande son megas de JSON
# muy repetitivo (se reduce en torno a 10 veces).
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Se añade el último para que quede por fuera de todo lo anterior: así hasta
# la respuesta del middleware de errores lleva sus cabeceras.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes_cors(),
    allow_methods=["GET", "POST"],
    # Authorization: sin ella el navegador no deja mandar el JWT desde :5173
    # (el backend y el frontend son orígenes distintos solo en desarrollo).
    allow_headers=["Content-Type", "Authorization"],
)

# Fase 4 de development: los 5 endpoints de este backend quedan autenticados,
# sin excepciones (aquí no hay nada público como el preview de imagen de
# OSINT). La dependencia va a nivel de router, así que routes.py no se toca:
# el módulo sigue funcionando igual si algún día se quita.
_auth = [Depends(get_current_user)]
app.include_router(tracking_router, dependencies=_auth)
app.include_router(tracking_lookup_router, dependencies=_auth)

# Solo trabajando en local con SQLite: rutas mínimas para crear y listar casos
# de prueba sin el backend de Casos (ver app/dev/casos_locales.py). Contra
# MySQL —la base compartida o la del despliegue— no se montan: ahí `cases` es
# del Módulo 1 y Tracking no expone ninguna forma de crear casos.
def usar_casos_locales(url: str) -> bool:
    return url.startswith("sqlite")


if usar_casos_locales(DATABASE_URL):
    from app.dev.casos_locales import router as casos_locales_router

    # Sin autenticar a propósito: solo existe contra SQLite local, donde no
    # hay backend de Casos que emita tokens. Contra MySQL ni siquiera se
    # monta, así que no abre nada en la base compartida ni en el despliegue.
    app.include_router(casos_locales_router)

# UI antigua sin build (iteración previa a React). Se mantiene accesible
# por referencia histórica, pero fuera de "/" para no suplantar al
# frontend oficial. Se monta antes que "/" para que no la tape.
_legacy_dir = Path(__file__).parent.parent / "legacy-frontend"
if _legacy_dir.exists():
    app.mount("/legacy", StaticFiles(directory=str(_legacy_dir), html=True), name="frontend-legacy")


# Frontend propio del módulo, EN DESUSO desde la integración en development.
#
# La interfaz oficial de Tracking es la del frontend único del repositorio
# común (`frontend/src/modules/tracking`), que es la que ve el perito. La
# copia de este módulo se conserva como referencia y para poder enseñarlo
# suelto, pero ya no se compila ni se sirve: mantener dos interfaces vivas es
# justo como se separaron las versiones la vez anterior.
#
# Para volver a servirla (demostración del módulo por separado):
#     TRACKING_FRONTEND_LOCAL=1   y compilarla antes (.\start-dev.ps1 -ConFrontend)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"


def servir_frontend_local() -> bool:
    return os.environ.get("TRACKING_FRONTEND_LOCAL", "").strip().lower() in {"1", "true", "si", "sí", "yes"}
# `/cases` (sin barra) es la pantalla de casos; `/cases/...` es la API.
_PREFIJOS_API = ("cases/", "docs/", "openapi")


# response_model=None: devuelve una Response ya construida (fichero o JSON),
# no un modelo Pydantic; sin esto FastAPI intenta deducirlo del tipo de
# retorno y falla al arrancar.
@app.get("/{ruta_spa:path}", include_in_schema=False, response_model=None)
def servir_frontend(ruta_spa: str) -> FileResponse | JSONResponse:
    """Sirve el frontend compilado, con respaldo a index.html.

    Va declarada la última a propósito: FastAPI resuelve las rutas en orden
    de registro, así que la API (`/cases/...`), `/docs` y `/legacy` ya han
    tenido su oportunidad antes de llegar aquí. Solo atiende lo que no
    encajó arriba.

    El respaldo a `index.html` es imprescindible porque el frontend usa
    enrutado de cliente: `/tracking` o `/timeline` no son ficheros, y sin
    esto recargar la página o entrar por URL directa devolvía un 404 de la
    API. Ojo al detalle de la barra final, que es lo que evita el choque:
    `/cases/` es la API (ruta registrada antes) y `/cases` es la pantalla
    de casos, que cae aquí.
    """
    # Una ruta de la API que no existe es un 404 de la API, no la pantalla de
    # la aplicación: antes `/cases/1/tracking/noexiste` devolvía index.html con
    # 200, y un cliente de la API recibía HTML creyendo que todo iba bien.
    if ruta_spa.startswith(_PREFIJOS_API):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    if not servir_frontend_local() or not _frontend_dist.exists():
        return JSONResponse(
            {
                "servicio": "Nexus — Módulo 3 (Tracking Post-Incidente)",
                "docs": "/docs",
                "interfaz": "La pantalla de Tracking vive en el frontend único de development "
                            "(frontend/src/modules/tracking). Este backend ya no sirve la suya.",
                "para_enseñarlo_suelto": "compílala con .\\start-dev.ps1 -ConFrontend "
                                         "y arranca con TRACKING_FRONTEND_LOCAL=1",
                "frontend_legacy": "/legacy",
            }
        )

    # Fichero real dentro de dist (assets, favicon...). resolve() + is_relative_to
    # evitan que una ruta con '..' saque ficheros de fuera del directorio.
    if ruta_spa:
        candidato = (_frontend_dist / ruta_spa).resolve()
        if candidato.is_file() and candidato.is_relative_to(_frontend_dist.resolve()):
            return FileResponse(candidato)

    return FileResponse(_frontend_dist / "index.html")
