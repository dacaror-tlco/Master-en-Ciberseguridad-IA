"""Modelo de base de datos para un caso de análisis de IP. Mismo patrón que los demás módulos."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IpCase(Base):
    __tablename__ = "ip_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ip: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    abuseipdb: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
