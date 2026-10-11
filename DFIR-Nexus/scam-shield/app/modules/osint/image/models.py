"""Modelos de base de datos del sub-módulo Imagen. Mismo patrón que los demás."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImageCase(Base):
    """
    Deliberadamente NO guardamos el archivo de imagen en sí (ni en disco ni en
    la base de datos) — solo su hash perceptual y los metadatos EXIF
    extraídos. `raw_file_sha256` es solo informativa (no participa en la
    cadena de custodia verificable, ver integrity/payloads.py).
    """
    __tablename__ = "image_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    perceptual_hash: Mapped[str] = mapped_column(String(64), index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)

    exif: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    raw_file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FacialSearchCase(Base):
    """
    Resultado de una búsqueda de reconocimiento facial (PimEyes) sobre un
    `ImageCase` ya existente. Tabla propia (no columna de ImageCase) por
    inmutabilidad de la cadena de custodia — ver docstring original en
    git history (app/models/facial_search_case.py) para el detalle legal
    completo (RGPD art. 9.2.f).
    """
    __tablename__ = "facial_search_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_case_id: Mapped[int] = mapped_column(Integer, index=True)
    source_sha256: Mapped[str] = mapped_column(String(64))

    confirmed_legal_basis: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ReverseImageSearchCase(Base):
    """
    Resultado de una búsqueda inversa de imagen (SerpApi) sobre un
    `ImageCase` ya existente. Tabla propia por el mismo motivo que
    `FacialSearchCase` (inmutabilidad de la cadena de custodia).
    """
    __tablename__ = "reverse_image_search_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_case_id: Mapped[int] = mapped_column(Integer, index=True)
    source_sha256: Mapped[str] = mapped_column(String(64))

    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
