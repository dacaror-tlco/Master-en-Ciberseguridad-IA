"""Orquestación de la verificación CNMV: refresco de caché + búsqueda + scoring + persistencia + cadena de custodia + registro en monitorización continua. Reutilizado por la ruta manual y por el scheduler de monitorización."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.osint.cnmv import cnmv_service, fca_register_service, registry_service, repository
from app.modules.osint.cnmv.models import CnmvCheckCase
from app.modules.osint.cnmv.risk_engine import evaluate_cnmv_risk
from app.modules.osint.cnmv.schemas import CnmvMatch, CnmvRegisteredEntity, FcaMatch
from app.modules.osint.findings import service as findings_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.monitoring import service as monitoring_service


def run_cnmv_check(db: Session, query: str, case_id: int | None = None) -> CnmvCheckCase:
    query = query.strip()
    if not query:
        raise ValueError("La búsqueda no puede estar vacía")

    errors = cnmv_service.ensure_cache_fresh(db)

    query_lower = query.lower()
    cached_warnings = repository.list_warnings(db)
    matches = [
        CnmvMatch(fecha=w.fecha, companias=w.companias, observaciones=w.observaciones)
        for w in cached_warnings if query_lower in w.companias.lower()
    ]

    fca_matches: list[FcaMatch] = []
    try:
        fca_matches = fca_register_service.search_firm(query)
    except Exception as exc:
        errors.append(f"FCA Register falló: {exc}")

    registry_matches: list[CnmvRegisteredEntity] | None = None
    try:
        registry_matches = registry_service.search_registered_entities(query)
    except Exception as exc:
        errors.append(f"Registro de entidades CNMV falló: {exc}")

    flags, score = evaluate_cnmv_risk(matches, fca_matches, registry_matches)

    case = CnmvCheckCase(
        query=query,
        case_id=case_id,
        match_count=len(matches),
        matches=[m.model_dump(mode="json") for m in matches],
        fca_matches=[m.model_dump(mode="json") for m in fca_matches],
        registry_matches=[m.model_dump(mode="json") for m in registry_matches] if registry_matches is not None else None,
        risk_score=score,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    case = repository.create_case(db, case)

    integrity_service.record_evidence(db, "cnmv", case.id, integrity_payloads.cnmv_payload(case))
    findings_service.record_finding(db, "cnmv", case)
    # Identificador normalizado (minúsculas) para que "Aichaintrader" y "aichaintrader"
    # se traten como el mismo sujeto monitorizado.
    monitoring_service.touch_subject(db, "cnmv", query_lower, case.id, score, flags)

    return case


def get_case(db: Session, case_id: int) -> CnmvCheckCase | None:
    return repository.get_case(db, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[CnmvCheckCase]:
    return repository.list_cases(db, skip, limit)


def cache_status(db: Session) -> dict:
    newest = repository.newest_warning(db)
    return {
        "cached_warnings": repository.count_warnings(db),
        "last_refreshed": newest.scraped_at.isoformat() if newest else None,
    }
