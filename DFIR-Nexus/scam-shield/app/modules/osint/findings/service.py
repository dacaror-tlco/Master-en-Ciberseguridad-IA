"""
Rellena y consulta `osint_findings`, el modelo de lectura que scam-shield
publica para el resto de módulos de Nexus (ver models.py y
docs/CONTRATO-DATOS.md).

`record_finding` se llama una vez por análisis terminado, justo después de
`integrity_service.record_evidence` en cada `*/service.py`.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.findings import subjects
from app.modules.osint.findings.models import OsintFinding
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.shared.risk_levels import risk_bucket

logger = logging.getLogger(__name__)

_MAX_TOP_FLAGS = 5
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _json_safe(payload: dict) -> dict:
    """El payload de integridad puede traer datetimes; los aplana a algo que quepa en una columna JSON."""
    return json.loads(json.dumps(payload, default=str, ensure_ascii=False))


def _top_flags(flags: list) -> list:
    ordered = sorted(flags, key=lambda f: _SEVERITY_RANK.get((f or {}).get("severity"), 3))
    return ordered[:_MAX_TOP_FLAGS]


def record_finding(db: Session, case_type: str, case) -> OsintFinding | None:
    """
    Proyecta un caso recién sellado a una fila de `osint_findings`.

    Es AUXILIAR: si algo falla aquí, se registra y se sigue — el análisis
    en sí ya está guardado y no debe romperse por un fallo del modelo de
    lectura. Devuelve la fila creada, o None si no se pudo.
    """
    spec = subjects.REGISTRY.get(case_type)
    if spec is None:
        logger.warning("record_finding: case_type desconocido %r, no se proyecta", case_type)
        return None

    try:
        subject_value = spec.extract(case)[:255]
        risk_score = getattr(case, "risk_score", 0) or 0
        risk_level = risk_bucket(risk_score)
        flags = list(getattr(case, "risk_flags", None) or [])
        analyzed_at = (
            getattr(case, "analyzed_at", None)
            or getattr(case, "requested_at", None)
            or datetime.now(timezone.utc)
        )

        payload_builder = integrity_payloads.REGISTRY.get(case_type)
        details = _json_safe(payload_builder[1](case)) if payload_builder else {}

        finding = OsintFinding(
            case_type=case_type,
            source_table=case.__tablename__,
            source_id=case.id,
            case_id=getattr(case, "case_id", None),
            subject_type=spec.subject_type,
            subject_value=subject_value,
            risk_score=risk_score,
            risk_level=risk_level,
            headline=subjects.build_headline(spec, subject_value, risk_level, risk_score),
            flag_count=len(flags),
            top_flags=_top_flags(flags),
            details=details,
            analyzed_at=analyzed_at,
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)
        return finding
    except Exception:  # noqa: BLE001 - proyección auxiliar, nunca debe tumbar un análisis
        logger.exception("record_finding falló para %s#%s", case_type, getattr(case, "id", "?"))
        db.rollback()
        return None


def list_findings(
    db: Session,
    *,
    case_type: str | None = None,
    subject_type: str | None = None,
    subject_value: str | None = None,
    case_id: int | None = None,
    risk_level: str | None = None,
    min_risk_score: int | None = None,
    since: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[OsintFinding]:
    query = db.query(OsintFinding)
    if case_type is not None:
        query = query.filter(OsintFinding.case_type == case_type)
    if subject_type is not None:
        query = query.filter(OsintFinding.subject_type == subject_type)
    if subject_value is not None:
        query = query.filter(OsintFinding.subject_value == subject_value)
    if case_id is not None:
        query = query.filter(OsintFinding.case_id == case_id)
    if risk_level is not None:
        query = query.filter(OsintFinding.risk_level == risk_level)
    if min_risk_score is not None:
        query = query.filter(OsintFinding.risk_score >= min_risk_score)
    if since is not None:
        query = query.filter(OsintFinding.analyzed_at >= since)
    return query.order_by(desc(OsintFinding.analyzed_at), desc(OsintFinding.id)).offset(skip).limit(limit).all()


def get_finding(db: Session, finding_id: int) -> OsintFinding | None:
    return db.query(OsintFinding).filter(OsintFinding.id == finding_id).first()
