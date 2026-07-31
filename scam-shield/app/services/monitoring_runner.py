"""
Capa de despacho de la monitorización continua: sabe qué función de
análisis corresponde a cada case_type y cuándo le toca a un sujeto.

Vive separada de monitoring_service.py para evitar un import circular:
los *_analysis_service.py llaman a `monitoring_service.touch_subject` al
terminar, así que monitoring_service no puede depender de ellos — este
módulo sí, porque es una capa por encima de ambos.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoredSubject, RiskAlert
from app.services.cnmv_analysis_service import run_cnmv_check
from app.services.domain_analysis_service import run_domain_analysis
from app.services.ip_analysis_service import run_ip_analysis
from app.services.phone_analysis_service import run_phone_analysis
from app.services.typosquatting_analysis_service import run_typosquatting_analysis
from app.services.wallet_analysis_service import run_wallet_analysis

# Cada runner recibe (db, identifier) y devuelve el caso persistido — exactamente
# la misma firma reducida para poder recorrerlos todos igual desde run_due_checks.
_RUNNERS = {
    "domain": lambda db, identifier: run_domain_analysis(db, identifier),
    "wallet": lambda db, identifier: run_wallet_analysis(db, identifier),
    "phone": lambda db, identifier: run_phone_analysis(db, identifier, "ES"),
    "typosquatting": lambda db, identifier: run_typosquatting_analysis(db, identifier),
    "cnmv": lambda db, identifier: run_cnmv_check(db, identifier),
    "ip": lambda db, identifier: run_ip_analysis(db, identifier),
}


def _is_due(subject: MonitoredSubject, now: datetime) -> bool:
    if not subject.enabled:
        return False
    if subject.last_checked_at is None:
        return True
    last_checked_at = subject.last_checked_at
    if last_checked_at.tzinfo is None:  # SQLite no conserva tz al releer (mismo caso que en cnmv_service.py)
        last_checked_at = last_checked_at.replace(tzinfo=timezone.utc)
    return (now - last_checked_at).total_seconds() >= subject.check_interval_hours * 3600


def check_subject_now(db: Session, subject_id: int) -> tuple[MonitoredSubject | None, RiskAlert | None, str | None]:
    """Fuerza un re-chequeo inmediato de un sujeto, sin esperar a que le toque. Devuelve (sujeto, alerta_o_None, error_o_None)."""
    subject = db.query(MonitoredSubject).filter(MonitoredSubject.id == subject_id).first()
    if subject is None:
        return None, None, None

    runner = _RUNNERS.get(subject.case_type)
    if runner is None:
        return subject, None, f"Tipo de sujeto desconocido: {subject.case_type}"

    try:
        runner(db, subject.identifier)  # el propio runner llama a touch_subject y persiste todo
    except Exception as exc:
        return subject, None, str(exc)

    db.refresh(subject)
    latest_alert = (
        db.query(RiskAlert)
        .filter(RiskAlert.subject_id == subject.id)
        .order_by(RiskAlert.detected_at.desc())
        .first()
    )
    # Solo se devuelve si es de esta misma pasada (mismo caso que acaba de quedar como "último" del sujeto).
    if latest_alert is not None and latest_alert.new_case_id == subject.last_case_id:
        return subject, latest_alert, None
    return subject, None, None


def run_due_checks(db: Session) -> dict:
    """Recorre los sujetos activos a los que ya les toca re-chequeo. Pensado para llamarse desde el scheduler en segundo plano."""
    now = datetime.now(timezone.utc)
    subjects = db.query(MonitoredSubject).filter(MonitoredSubject.enabled.is_(True)).all()

    checked = 0
    errors: list[str] = []

    for subject in subjects:
        if not _is_due(subject, now):
            continue
        runner = _RUNNERS.get(subject.case_type)
        if runner is None:
            continue
        try:
            runner(db, subject.identifier)
            checked += 1
        except Exception as exc:
            errors.append(f"{subject.case_type}:{subject.identifier} -> {exc}")
            # Se anota igualmente el intento, para no reintentar en bucle si la fuente externa está caída.
            subject.last_checked_at = now
            db.commit()

    return {"checked": checked, "errors": errors}
