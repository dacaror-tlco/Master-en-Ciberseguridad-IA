import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core import scheduler as scheduler_module
from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.osint.case_link import routes as case_link
from app.modules.osint.cnmv import models as cnmv_models  # noqa: F401
from app.modules.osint.cnmv import routes as cnmv
from app.modules.osint.domain import models as domain_models  # noqa: F401
from app.modules.osint.domain import routes as analysis
from app.modules.osint.findings import models as findings_models  # noqa: F401
from app.modules.osint.findings import routes as findings
from app.modules.osint.email import models as email_models  # noqa: F401
from app.modules.osint.email import routes as email_analysis
from app.modules.osint.image import models as image_models  # noqa: F401
from app.modules.osint.image import routes as image_analysis
from app.modules.osint.integrity import models as integrity_models  # noqa: F401
from app.modules.osint.integrity import routes as integrity
from app.modules.osint.ip import models as ip_models  # noqa: F401
from app.modules.osint.ip import routes as ip_analysis
from app.modules.osint.monitoring import models as monitoring_models  # noqa: F401
from app.modules.osint.monitoring import routes as monitoring
from app.modules.osint.phone import models as phone_models  # noqa: F401
from app.modules.osint.phone import routes as phone_analysis
from app.modules.osint.report import routes as report
from app.modules.osint.typosquatting import models as typosquatting_models  # noqa: F401
from app.modules.osint.typosquatting import routes as typosquatting
from app.modules.osint.wallet import models as wallet_models  # noqa: F401
from app.modules.osint.wallet import routes as wallet_analysis


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_module.start_scheduler()
    yield
    scheduler_module.stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    description="Herramienta de recolección de evidencias y análisis de riesgo de estafas online.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def convertir_errores_no_controlados(request: Request, call_next):
    """
    Sin esto, una excepción no controlada (p. ej. no poder conectar con
    MySQL) se propaga como un 500 "en bruto" que no pasa por
    CORSMiddleware, y el navegador lo reporta como un bloqueo de CORS en
    vez de como el error real que es. Ver docs/INTEGRACION_Y_DESPLIEGUE.md.
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# Fase final (hardening): restringido al único origen desde el que corre
# el frontend en desarrollo (mismo valor que ya usaba app/main.py de
# Casos) — antes era "*". En producción esto no protege nada nuevo NI
# hace falta tocarlo: el navegador solo habla con el origen del gateway
# (ver deploy/gateway/nginx.conf), nunca directamente con este backend,
# así que ninguna petición real llega a evaluar esta cabecera; la
# restricción de abajo es puramente defensa en profundidad para cuando
# este backend se expone directamente en desarrollo local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# El esquema ya no se crea aquí: lo gestiona Alembic (ver alembic/env.py y
# alembic/versions/) — mismo patrón que el resto de módulos de Nexus.
# `alembic upgrade head` antes de arrancar la app, en local y en despliegue.

# Fase 4: autenticación aplicada a nivel de router (dependencies=[...] de
# include_router), no tocando cada función de ruta una por una — ninguna
# de las de abajo tiene una excepción interna, así que no hace falta.
# ÚNICA excepción real: `image_analysis.router` NO lleva dependencia aquí
# porque una de sus rutas (GET /analysis/image/preview/{token}) debe
# seguir siendo pública (la consume SerpApi por URL, sin poder llevar
# ninguna cabecera Authorization) — sus otras 3 rutas ya llevan
# Depends(get_current_user) puesto directamente en la función, en
# app/modules/osint/image/routes.py. `image_analysis.cases_router` es un
# router aparte, sin esa excepción, así que sí lleva la dependencia aquí.
_auth = [Depends(get_current_user)]

app.include_router(analysis.router, dependencies=_auth)
app.include_router(analysis.cases_router, dependencies=_auth)
app.include_router(email_analysis.router, dependencies=_auth)
app.include_router(email_analysis.cases_router, dependencies=_auth)
app.include_router(wallet_analysis.router, dependencies=_auth)
app.include_router(wallet_analysis.cases_router, dependencies=_auth)
app.include_router(report.router, dependencies=_auth)
app.include_router(report.consolidated_router, dependencies=_auth)
app.include_router(typosquatting.router, dependencies=_auth)
app.include_router(typosquatting.cases_router, dependencies=_auth)
app.include_router(phone_analysis.router, dependencies=_auth)
app.include_router(phone_analysis.cases_router, dependencies=_auth)
app.include_router(cnmv.router, dependencies=_auth)
app.include_router(cnmv.cases_router, dependencies=_auth)
app.include_router(cnmv.warnings_router, dependencies=_auth)
app.include_router(image_analysis.router)  # ver nota arriba: sin dependencia a nivel de router
app.include_router(image_analysis.cases_router, dependencies=_auth)
app.include_router(ip_analysis.router, dependencies=_auth)
app.include_router(ip_analysis.cases_router, dependencies=_auth)
app.include_router(integrity.router, dependencies=_auth)
app.include_router(monitoring.router, dependencies=_auth)
app.include_router(monitoring.alerts_router, dependencies=_auth)
app.include_router(findings.router, dependencies=_auth)
app.include_router(case_link.router, dependencies=_auth)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


# Sirve el frontend ya compilado (`npm run build` -> frontend/dist) desde el
# propio backend. Se monta al final para que no tape ninguna ruta de la API:
# solo responde a lo que no haya encajado ya arriba. Esto permite desplegar
# detrás de un único subdominio (mismo origen -> sin CORS). En desarrollo, el
# frontend se sirve con `npm run dev` (Vite, puerto 5173) en vez de esto —
# `check_dir=False` para que levantar solo el backend no falle si nadie ha
# corrido `npm run build` todavía (frontend/dist no existe).
app.mount("/", StaticFiles(directory="frontend/dist", html=True, check_dir=False), name="frontend")
