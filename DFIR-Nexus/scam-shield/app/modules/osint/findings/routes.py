"""
API de lectura de `osint_findings`.

Es el punto de entrada estable para el resto de módulos de Nexus que
prefieran HTTP a leer la tabla directamente (ver docs/CONTRATO-DATOS.md).
Solo lectura: los findings los escribe scam-shield al terminar cada
análisis, nadie más.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.findings import service
from app.modules.osint.findings.schemas import FindingDetail, FindingListItem

router = APIRouter(prefix="/osint-findings", tags=["osint-findings"])


@router.get("", response_model=list[FindingListItem])
def list_findings(
    case_type: str | None = Query(None, description="domain | email | wallet | typosquatting | phone | cnmv | ip | image | image_reverse_search | image_facial_search"),
    subject_type: str | None = Query(None, description="domain | email_address | crypto_wallet | ip_address | phone_number | entity_name | image_file"),
    subject_value: str | None = Query(None, description="Identificador exacto (dominio, dirección, IP...)"),
    case_id: int | None = Query(None, description="Expediente de Nexus (cases.id) al que está atado el análisis"),
    risk_level: str | None = Query(None, description="low | medium | high"),
    min_risk_score: int | None = Query(None, ge=0, le=100),
    since: datetime | None = Query(None, description="Solo análisis con analyzed_at >= esta fecha (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return service.list_findings(
        db,
        case_type=case_type,
        subject_type=subject_type,
        subject_value=subject_value,
        case_id=case_id,
        risk_level=risk_level,
        min_risk_score=min_risk_score,
        since=since,
        skip=skip,
        limit=limit,
    )


@router.get("/{finding_id}", response_model=FindingDetail)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = service.get_finding(db, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"No existe el finding {finding_id}")
    return finding
