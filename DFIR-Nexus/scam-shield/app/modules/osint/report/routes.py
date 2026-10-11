from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.report import service
from app.modules.osint.report.schemas import ConsolidatedRequest, ConsolidatedResponse, ReportRequest

# Antes "/reports": colisionaba en namespace con /reports de Informes
# (Módulo 5), el propietario real de esa ruta en la integración de Nexus
# (Fase 4, ver docs/CONTRATOS.md). Este endpoint genera un PDF de riesgo
# propio de OSINT (no toca la tabla `reports`), así que pasa a vivir bajo
# el mismo prefijo /analysis que el resto de este módulo.
router = APIRouter(prefix="/analysis/reports", tags=["reports"])
consolidated_router = APIRouter(prefix="/analysis", tags=["consolidated"])


@router.post("/generate")
def generate_report(payload: ReportRequest, db: Session = Depends(get_db)) -> Response:
    pdf_bytes = service.generate_report_pdf(db, payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="informe_scamshield.pdf"'},
    )


@consolidated_router.post("/consolidated", response_model=ConsolidatedResponse)
def consolidated_assessment(payload: ConsolidatedRequest, db: Session = Depends(get_db)) -> ConsolidatedResponse:
    return service.consolidated_assessment(db, payload)
