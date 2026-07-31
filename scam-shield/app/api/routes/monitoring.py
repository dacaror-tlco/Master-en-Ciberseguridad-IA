from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.monitoring import (
    CheckNowResponse,
    MonitoredSubjectResponse,
    MonitoredSubjectUpdateRequest,
    RiskAlertResponse,
)
from app.services import monitoring_runner, monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
alerts_router = APIRouter(prefix="/alerts", tags=["monitoring"])


@router.get("/subjects", response_model=list[MonitoredSubjectResponse])
def list_monitored_subjects(case_type: str | None = None, db: Session = Depends(get_db)):
    return monitoring_service.list_subjects(db, case_type)


@router.patch("/subjects/{subject_id}", response_model=MonitoredSubjectResponse)
def update_monitored_subject(subject_id: int, payload: MonitoredSubjectUpdateRequest, db: Session = Depends(get_db)):
    subject = monitoring_service.update_subject(db, subject_id, payload.enabled, payload.check_interval_hours)
    if subject is None:
        raise HTTPException(status_code=404, detail=f"No existe el sujeto monitorizado {subject_id}")
    return subject


@router.post("/subjects/{subject_id}/check-now", response_model=CheckNowResponse)
def check_monitored_subject_now(subject_id: int, db: Session = Depends(get_db)):
    subject, alert, error = monitoring_runner.check_subject_now(db, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail=f"No existe el sujeto monitorizado {subject_id}")
    return CheckNowResponse(subject=subject, alert=alert, error=error)


@alerts_router.get("", response_model=list[RiskAlertResponse])
def list_alerts(unacknowledged_only: bool = False, db: Session = Depends(get_db)):
    return monitoring_service.list_alerts(db, unacknowledged_only)


@alerts_router.post("/{alert_id}/acknowledge", response_model=RiskAlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = monitoring_service.acknowledge_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"No existe la alerta {alert_id}")
    return alert
