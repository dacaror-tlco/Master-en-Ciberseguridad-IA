from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.integrity_ledger import IntegrityLedgerEntry
from app.schemas.integrity import ChainVerificationResponse, IntegrityLedgerEntryResponse
from app.services import integrity_service

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/verify", response_model=ChainVerificationResponse)
def verify_integrity_chain(db: Session = Depends(get_db)):
    intact, broken_at = integrity_service.verify_chain(db)
    total = db.query(IntegrityLedgerEntry).count()

    if total == 0:
        message = "La cadena está vacía todavía (no se ha analizado ningún caso)."
    elif intact:
        message = f"Cadena íntegra: los {total} eslabones registrados coinciden con sus huellas originales."
    else:
        message = f"⚠️ La cadena está rota a partir del eslabón #{broken_at} — el contenido de esa evidencia no coincide con lo registrado en su momento."

    return ChainVerificationResponse(intact=intact, total_entries=total, broken_at_entry_id=broken_at, message=message)


@router.get("/ledger", response_model=list[IntegrityLedgerEntryResponse])
def list_ledger(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(IntegrityLedgerEntry)
        .order_by(asc(IntegrityLedgerEntry.id))
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/case/{case_type}/{case_id}", response_model=IntegrityLedgerEntryResponse)
def get_case_certificate(case_type: str, case_id: int, db: Session = Depends(get_db)):
    entry = integrity_service.get_entry_for_case(db, case_type, case_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"No hay ningún registro de integridad para {case_type}#{case_id}")
    return entry
