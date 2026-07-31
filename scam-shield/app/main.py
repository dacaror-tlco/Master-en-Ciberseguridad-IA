from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analysis, cases, cnmv, consolidated, email_analysis, image_analysis, integrity, ip_analysis, monitoring, phone_analysis, report, typosquatting, wallet_analysis
from app.core import scheduler as scheduler_module
from app.core.config import settings
from app.core.database import Base, engine
from app.models import case, cnmv_check_case, cnmv_warning, email_case, facial_search_case, image_case, integrity_ledger, ip_case, ofac_sanctioned_address, phone_case, reverse_image_search_case, typosquatting_case, wallet_case  # noqa: F401 - necesario para que SQLAlchemy registre los modelos antes de create_all
from app.models import monitoring as monitoring_models  # noqa: F401 - idem, MonitoredSubject/RiskAlert


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

# En producción, restringir a los dominios reales del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fase 1: crear tablas directamente al arrancar. Cuando el esquema empiece
# a cambiar con frecuencia (fase 2 en adelante), pasaremos a Alembic para
# tener migraciones versionadas en vez de esto.
Base.metadata.create_all(bind=engine)

app.include_router(analysis.router)
app.include_router(cases.router)
app.include_router(email_analysis.router)
app.include_router(email_analysis.cases_router)
app.include_router(wallet_analysis.router)
app.include_router(wallet_analysis.cases_router)
app.include_router(report.router)
app.include_router(consolidated.router)
app.include_router(typosquatting.router)
app.include_router(typosquatting.cases_router)
app.include_router(phone_analysis.router)
app.include_router(phone_analysis.cases_router)
app.include_router(cnmv.router)
app.include_router(cnmv.cases_router)
app.include_router(cnmv.warnings_router)
app.include_router(image_analysis.router)
app.include_router(image_analysis.cases_router)
app.include_router(ip_analysis.router)
app.include_router(ip_analysis.cases_router)
app.include_router(integrity.router)
app.include_router(monitoring.router)
app.include_router(monitoring.alerts_router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


# Sirve el frontend estático desde el propio backend. Se monta al final para
# que no tape ninguna ruta de la API: solo responde a lo que no haya
# encajado ya arriba. Esto permite desplegar detrás de un único
# subdominio (mismo origen -> sin CORS) sin afectar al uso local habitual
# de abrir frontend/index.html directamente con doble clic.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
