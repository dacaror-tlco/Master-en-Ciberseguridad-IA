"""Modelos de base de datos del sub-módulo CNMV. Mismo patrón que los demás."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CnmvCheckCase(Base):
    __tablename__ = "cnmv_check_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(255), index=True)
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer)

    matches: Mapped[list] = mapped_column(JSON, default=list)
    fca_matches: Mapped[list | None] = mapped_column(JSON, nullable=True)
    registry_matches: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus (Módulo
    # 1) — esa tabla vive en otra base de datos hasta que los módulos se
    # fusionen de verdad. Mismo patrón que `timeline_events.origen_id` en el
    # CLAUDE.md de la rama modulo-casos.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CnmvWarning(Base):
    """
    Caché local de advertencias de la CNMV.

    La CNMV no ofrece una API — es un listado HTML público de ~358 páginas.
    Scrapearlo entero en cada búsqueda sería lentísimo e innecesario, así que
    mantenemos una copia local de las advertencias más recientes, que se
    refresca sola cuando caduca (ver cnmv_service.py / routes.py).
    """
    __tablename__ = "cnmv_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[str] = mapped_column(String(32))  # tal cual la publica la CNMV, "dd/mm/aaaa"
    companias: Mapped[str] = mapped_column(Text)  # texto completo de la celda, puede incluir varias URLs/nombres
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
