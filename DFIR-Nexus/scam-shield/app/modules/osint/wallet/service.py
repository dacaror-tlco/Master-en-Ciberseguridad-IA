"""Orquestación del análisis de wallet: consulta blockchain + scoring + persistencia + cadena de custodia + registro en monitorización continua. Reutilizado por la ruta manual y por el scheduler de monitorización."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.osint.wallet import ofac_service, repository, wallet_service
from app.modules.osint.wallet.models import WalletCase
from app.modules.osint.wallet.risk_engine import evaluate_wallet_risk
from app.modules.osint.findings import service as findings_service
from app.modules.osint.integrity import payloads as integrity_payloads
from app.modules.osint.integrity import service as integrity_service
from app.modules.osint.monitoring import service as monitoring_service


def run_wallet_analysis(db: Session, address: str, case_id: int | None = None) -> WalletCase:
    address = address.strip()

    # ValueError (formato no reconocido) y otras excepciones (fallo de red) se
    # dejan subir tal cual: quien llame decide cómo traducirlas (código HTTP
    # en la ruta manual, entrada en `errors` en el runner de monitorización).
    wallet_info = wallet_service.get_wallet_info(address)

    # El cruce OFAC es un enriquecimiento opcional: si falla (red caída, etc.)
    # se registra como error pero no impide completar el análisis con lo que
    # ya tenemos del histórico de la propia blockchain.
    errors = ofac_service.ensure_cache_fresh(db)
    try:
        wallet_info.ofac_sanctioned = ofac_service.is_sanctioned(db, address, wallet_info.chain)
    except Exception as exc:
        errors.append(f"No se pudo comprobar la lista OFAC: {exc}")

    flags, score = evaluate_wallet_risk(wallet_info)

    case = WalletCase(
        chain=wallet_info.chain,
        address=address,
        risk_score=score,
        case_id=case_id,
        wallet=wallet_info.model_dump(mode="json"),
        risk_flags=[f.model_dump(mode="json") for f in flags],
        errors=errors,
        analyzed_at=datetime.now(timezone.utc),
    )
    case = repository.create_case(db, case)

    integrity_service.record_evidence(db, "wallet", case.id, integrity_payloads.wallet_payload(case))
    findings_service.record_finding(db, "wallet", case)
    monitoring_service.touch_subject(db, "wallet", address, case.id, score, flags)

    return case


def get_case(db: Session, case_id: int) -> WalletCase | None:
    return repository.get_case(db, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[WalletCase]:
    return repository.list_cases(db, skip, limit)
