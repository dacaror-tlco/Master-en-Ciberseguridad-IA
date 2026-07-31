"""
Motor de monitorización continua.

Cada vez que se analiza un sujeto (dominio, wallet, teléfono, dominio
protegido frente a typosquatting, búsqueda CNMV) — ya sea a mano desde la
API o automáticamente desde el scheduler — se registra/actualiza su
MonitoredSubject y se compara el resultado con el chequeo anterior. Si el
nivel de riesgo ha subido de forma relevante, se genera una RiskAlert.

Importante: este módulo NUNCA modifica un caso ya guardado (eso rompería
la cadena de custodia, ver integrity_service.py). Cada re-chequeo crea un
caso nuevo a través del mismo pipeline que el análisis manual —
MonitoredSubject solo guarda el puntero al último y su score, para poder
comparar.

Este módulo es deliberadamente "de bajo nivel": no sabe re-ejecutar un
análisis (eso vive en monitoring_runner.py, en una capa separada para
evitar un import circular — los *_analysis_service.py llaman a
`touch_subject` al terminar, así que este módulo no puede depender de
ellos).
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.monitoring import MonitoredSubject, RiskAlert
from app.schemas.domain_analysis import RiskFlag

_BUCKET_RANK = {"low": 0, "medium": 1, "high": 2}


def risk_bucket(score: int) -> str:
    """Mismos cortes que el frontend (riskLevel en index.html), para que 'ha cambiado de nivel' signifique lo mismo en toda la herramienta."""
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def get_or_create_subject(db: Session, case_type: str, identifier: str) -> MonitoredSubject:
    subject = (
        db.query(MonitoredSubject)
        .filter(MonitoredSubject.case_type == case_type, MonitoredSubject.identifier == identifier)
        .first()
    )
    if subject is None:
        subject = MonitoredSubject(
            case_type=case_type,
            identifier=identifier,
            enabled=True,
            check_interval_hours=settings.monitoring_default_interval_hours,
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)
    return subject


def touch_subject(
    db: Session, case_type: str, identifier: str, case_id: int, score: int, flags: list[RiskFlag]
) -> RiskAlert | None:
    """
    Se llama justo después de persistir cualquier caso nuevo (análisis
    manual o re-chequeo del scheduler). Registra/actualiza el sujeto
    monitorizado y devuelve una RiskAlert si el riesgo ha subido de forma
    relevante respecto al chequeo anterior (None la primera vez que se ve
    el sujeto, o si no hay cambio relevante).
    """
    subject = get_or_create_subject(db, case_type, identifier)

    previous_case_id = subject.last_case_id
    previous_score = subject.last_score
    previous_bucket = subject.last_bucket
    new_bucket = risk_bucket(score)

    alert = None
    if previous_score is not None:
        bucket_worsened = _BUCKET_RANK.get(new_bucket, -1) > _BUCKET_RANK.get(previous_bucket, -1)
        score_jump = (score - previous_score) >= settings.monitoring_score_change_threshold
        if bucket_worsened or score_jump:
            reason = (
                f"El nivel de riesgo pasó de {previous_bucket} a {new_bucket} (score {previous_score} -> {score})"
                if bucket_worsened
                else f"El score subió {score - previous_score} puntos sin cambiar de nivel (de {previous_score} a {score})"
            )
            alert = RiskAlert(
                subject_id=subject.id,
                case_type=case_type,
                identifier=identifier,
                previous_case_id=previous_case_id,
                previous_score=previous_score,
                previous_bucket=previous_bucket,
                new_case_id=case_id,
                new_score=score,
                new_bucket=new_bucket,
                reason=reason,
                new_flag_codes=[f.code for f in flags],
                detected_at=datetime.now(timezone.utc),
            )
            db.add(alert)

    subject.last_case_id = case_id
    subject.last_score = score
    subject.last_bucket = new_bucket
    subject.last_checked_at = datetime.now(timezone.utc)
    db.commit()
    if alert is not None:
        db.refresh(alert)

    return alert


def list_subjects(db: Session, case_type: str | None = None) -> list[MonitoredSubject]:
    query = db.query(MonitoredSubject)
    if case_type:
        query = query.filter(MonitoredSubject.case_type == case_type)
    return query.order_by(MonitoredSubject.case_type, MonitoredSubject.identifier).all()


def update_subject(
    db: Session, subject_id: int, enabled: bool | None, check_interval_hours: int | None
) -> MonitoredSubject | None:
    subject = db.query(MonitoredSubject).filter(MonitoredSubject.id == subject_id).first()
    if subject is None:
        return None
    if enabled is not None:
        subject.enabled = enabled
    if check_interval_hours is not None:
        subject.check_interval_hours = check_interval_hours
    db.commit()
    db.refresh(subject)
    return subject


def list_alerts(db: Session, unacknowledged_only: bool = False) -> list[RiskAlert]:
    query = db.query(RiskAlert)
    if unacknowledged_only:
        query = query.filter(RiskAlert.acknowledged.is_(False))
    return query.order_by(RiskAlert.detected_at.desc()).all()


def acknowledge_alert(db: Session, alert_id: int) -> RiskAlert | None:
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if alert is None:
        return None
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert
