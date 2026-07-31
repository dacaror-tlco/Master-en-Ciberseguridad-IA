"""
Orquestación de la verificación CNMV: refresco de caché + búsqueda +
scoring + persistencia + cadena de custodia + registro en monitorización
continua. Reutilizado por la ruta manual y por el scheduler de monitorización.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.cnmv_check_case import CnmvCheckCase
from app.models.cnmv_warning import CnmvWarning
from app.schemas.cnmv import CnmvMatch, CnmvRegisteredEntity, FcaMatch
from app.services import cnmv_registry_service, cnmv_service, fca_register_service, integrity_payloads, integrity_service, monitoring_service
from app.services.cnmv_risk_engine import evaluate_cnmv_risk


def run_cnmv_check(db: Session, query: str) -> CnmvCheckCase:
    query = query.strip()
    if not query:
        raise ValueError("La búsqueda no puede estar vacía")

    errors = cnmv_service.ensure_cache_fresh(db)

    query_lower = query.lower()
    cached_warnings = db.query(CnmvWarning).all()
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
        registry_matches = cnmv_registry_service.search_registered_entities(query)
    except Exception as exc:
        errors.append(f"Registro de entidades CNMV falló: {exc}")

    flags, score = evaluate_cnmv_risk(matches, fca_matches, registry_matches)

    case = CnmvCheckCase(
        query=query,
        match_count=len(matches),
        matches=[m.model_dump(mode="json") for m in matches],
        fca_matches=[m.model_dump(mode="json") for m in fca_matches],
        registry_matches=[m.model_dump(mode="json") for m in registry_matches] if registry_matches is not None else None,
        risk_score=score,
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    integrity_service.record_evidence(db, "cnmv", case.id, integrity_payloads.cnmv_payload(case))
    # Identificador normalizado (minúsculas) para que "Aichaintrader" y "aichaintrader"
    # se traten como el mismo sujeto monitorizado.
    monitoring_service.touch_subject(db, "cnmv", query_lower, case.id, score, flags)

    return case
