"""
Caché local de advertencias de la CNMV.

La CNMV no ofrece una API — es un listado HTML público de ~358 páginas.
Scrapearlo entero en cada búsqueda sería lentísimo e innecesario, así que
mantenemos una copia local de las advertencias más recientes, que se
refresca sola cuando caduca (ver cnmv_service.py / api/routes/cnmv.py).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CnmvWarning(Base):
    __tablename__ = "cnmv_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[str] = mapped_column(String)  # tal cual la publica la CNMV, "dd/mm/aaaa"
    companias: Mapped[str] = mapped_column(Text)  # texto completo de la celda, puede incluir varias URLs/nombres
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
