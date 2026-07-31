"""
Resultado de una búsqueda de reconocimiento facial (PimEyes) sobre un
`ImageCase` ya existente.

Ver el docstring de `reverse_image_search_case.py` para por qué esto es una
tabla propia y no una columna añadida a `ImageCase` (inmutabilidad de la
cadena de custodia).

Esta acción está deliberadamente acotada respecto al resto del análisis de
imagen — ver la sección "Reconocimiento facial (PimEyes) — uso acotado" del
README para la justificación legal y ética completa. En corto: NO es una
señal automática del análisis por defecto, sino una acción separada que
alguien tiene que decidir ejecutar explícitamente para un caso concreto, y
que exige confirmar (`confirmed_legal_basis`) que ese uso está amparado por
una base legal (art. 9.2.f RGPD — ejercicio de reclamaciones legales, ej.
documentar una usurpación de identidad para una denuncia). Esa confirmación
queda sellada para siempre junto con los resultados en el ledger de
integridad — no se puede alegar después que la búsqueda se hizo sin dejar
rastro, ni editar `notes`/resultados a posteriori sin romper la cadena.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FacialSearchCase(Base):
    __tablename__ = "facial_search_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_case_id: Mapped[int] = mapped_column(Integer, index=True)
    source_sha256: Mapped[str] = mapped_column(String)

    confirmed_legal_basis: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
