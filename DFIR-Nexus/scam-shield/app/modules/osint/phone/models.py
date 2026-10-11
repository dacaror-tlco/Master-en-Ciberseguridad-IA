"""Modelo de base de datos para un caso de análisis de teléfono. Mismo patrón que los demás módulos."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PhoneCase(Base):
    __tablename__ = "phone_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_phone: Mapped[str] = mapped_column(String(32), index=True)
    line_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus — ver
    # el mismo campo en domain/models.py para la explicación completa.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    phone: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    community_reports: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fraud_score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    carrier_intelligence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
