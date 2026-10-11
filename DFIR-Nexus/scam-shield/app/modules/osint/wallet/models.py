"""Modelos de base de datos del sub-módulo Wallet. Mismo patrón que los demás."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletCase(Base):
    __tablename__ = "wallet_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chain: Mapped[str] = mapped_column(String(16))
    address: Mapped[str] = mapped_column(String(128), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    wallet: Mapped[dict] = mapped_column(JSON)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class OfacSanctionedAddress(Base):
    """
    Caché local de direcciones cripto sancionadas por la OFAC (Tesoro de
    EEUU) — ver ofac_service.py para el origen de los datos y el refresco.
    """
    __tablename__ = "ofac_sanctioned_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(128), index=True)
    asset: Mapped[str] = mapped_column(String(16))  # "BTC" | "ETH" | "TRON"
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
