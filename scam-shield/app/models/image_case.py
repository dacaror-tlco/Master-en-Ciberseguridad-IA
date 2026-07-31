"""
Modelo de base de datos para un caso de análisis de imagen.

Deliberadamente NO guardamos el archivo de imagen en sí (ni en disco ni en
la base de datos) — solo su hash perceptual y los metadatos EXIF
extraídos. Esto evita hinchar la base de datos con binarios y, sobre
todo, evita acumular una colección de fotos de gente (aunque sea con
buena intención) más tiempo del estrictamente necesario para el análisis.

`raw_file_sha256`: huella del ARCHIVO original en el momento de la
captura. Es solo informativa (para que el usuario compare su copia
original si la conserva) — NO participa en la cadena de custodia
verificable (integrity_service.py) por el mismo motivo que en EmailCase:
no se puede recalcular sin conservar el archivo, así que "verificarla"
más adelante daría siempre un falso positivo de manipulación.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImageCase(Base):
    __tablename__ = "image_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    perceptual_hash: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)

    exif: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    raw_file_sha256: Mapped[str | None] = mapped_column(String, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
