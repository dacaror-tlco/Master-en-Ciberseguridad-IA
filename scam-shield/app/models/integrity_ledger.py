"""
Libro de registro de la cadena de custodia (ver integrity_service.py para
la lógica de encadenado). Una única tabla, compartida por todos los
módulos: cada análisis completado (de cualquier tipo) añade un eslabón.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IntegrityLedgerEntry(Base):
    __tablename__ = "integrity_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_type: Mapped[str] = mapped_column(String, index=True)  # "domain" | "email" | "wallet" | "typosquatting" | "phone" | "cnmv" | "image"
    case_id: Mapped[int] = mapped_column(Integer, index=True)

    evidence_hash: Mapped[str] = mapped_column(String)          # SHA-256 del contenido de esta evidencia concreta
    previous_chain_hash: Mapped[str] = mapped_column(String)    # chain_hash del eslabón anterior (o "0"*64 si es el primero)
    chain_hash: Mapped[str] = mapped_column(String, index=True)  # SHA-256(previous_chain_hash + evidence_hash)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
