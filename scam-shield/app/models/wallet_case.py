"""
Modelo de base de datos para un caso de análisis de wallet cripto.
Mismo patrón que Case y EmailCase: detalle en JSON para iterar rápido.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletCase(Base):
    __tablename__ = "wallet_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chain: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    wallet: Mapped[dict] = mapped_column(JSON)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
