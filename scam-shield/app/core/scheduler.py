"""
Scheduler en el mismo proceso (APScheduler) para la re-comprobación
periódica de los sujetos monitorizados.

Fase 1 del proyecto: sin Celery/Redis todavía (ver "Próximos pasos" en el
README), así que esto corre dentro del propio proceso de uvicorn —
suficiente para un solo worker. Si en el futuro se despliega con varios
workers, cada uno lanzaría su propio scheduler y se duplicarían los
chequeos; ese es el momento de pasar a una cola de tareas externa
compartida (Celery + Redis).
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.services import image_cache, monitoring_runner

logger = logging.getLogger("scamshield.scheduler")

scheduler = BackgroundScheduler()

_JOB_ID = "monitoring_due_checks"
_IMAGE_CACHE_PURGE_JOB_ID = "image_cache_purge"


def _run_due_checks_job() -> None:
    db = SessionLocal()
    try:
        result = monitoring_runner.run_due_checks(db)
        if result["checked"] or result["errors"]:
            logger.info(
                "Monitorización: %s sujeto(s) re-chequeado(s), %s error(es)",
                result["checked"],
                len(result["errors"]),
            )
    finally:
        db.close()


def _purge_image_cache_job() -> None:
    # Higiene: la caché ya purga perezosamente en cada get()/consume(), esto
    # solo evita que entradas caducadas y nunca vueltas a pedir se queden en
    # memoria indefinidamente.
    image_cache.purge_expired()


def start_scheduler() -> None:
    if scheduler.running:
        return
    if settings.monitoring_enabled:
        scheduler.add_job(
            _run_due_checks_job,
            "interval",
            minutes=settings.monitoring_scheduler_interval_minutes,
            id=_JOB_ID,
            replace_existing=True,
        )
    scheduler.add_job(
        _purge_image_cache_job,
        "interval",
        minutes=5,
        id=_IMAGE_CACHE_PURGE_JOB_ID,
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
