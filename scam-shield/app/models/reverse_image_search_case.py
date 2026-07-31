"""
Resultado de una búsqueda inversa de imagen (SerpApi) sobre un `ImageCase`
ya existente.

Es una tabla propia, separada de `ImageCase`, a propósito: el sistema de
cadena de custodia (`integrity_service.py`) asume que cada fila de caso es
inmutable una vez sellada en el ledger — si esto fuera una columna más de
`ImageCase` rellenada más tarde, `verify_chain` volvería a calcular el hash
del caso original con datos distintos a los sellados y lo marcaría como
"manipulado" sin que hubiera manipulación real. En vez de eso, esta
búsqueda se sella como su propio eslabón independiente (`case_type =
"image_reverse_search"`), enlazado al caso de imagen original solo de
forma lógica por `image_case_id` (mismo estilo que usa `IntegrityLedgerEntry`
para enlazar `case_type` + `case_id`, sin claves foráneas reales entre
tablas de casos).
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReverseImageSearchCase(Base):
    __tablename__ = "reverse_image_search_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_case_id: Mapped[int] = mapped_column(Integer, index=True)
    source_sha256: Mapped[str] = mapped_column(String)

    matches: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
