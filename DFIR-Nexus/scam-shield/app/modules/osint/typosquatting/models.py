"""Modelo de base de datos para un caso de typosquatting. Mismo patrón que los demás módulos."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TyposquattingCase(Base):
    __tablename__ = "typosquatting_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus — ver
    # el mismo campo en domain/models.py para la explicación completa.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    variants_generated: Mapped[int] = mapped_column(Integer, default=0)
    resolved_count: Mapped[int] = mapped_column(Integer, default=0)
    candidates: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
