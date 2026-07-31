"""
Modelo de base de datos para un "caso".

Guardamos el resultado completo del análisis (WHOIS, SSL, flags, score)
como JSON en vez de crear una tabla por cada tipo de dato. Es una decisión
deliberada para la fase 1: nos deja avanzar rápido y añadir nuevos módulos
de análisis (email, cripto...) sin migraciones de esquema constantes.
Si en el futuro necesitamos consultar/filtrar por campos concretos del
WHOIS a gran escala, normalizaremos esas columnas entonces.

`dns`, `ip_reputations`, `crtsh` y `wayback` se añadieron después de los
campos originales — nullable / con default, mismo motivo que
`resolved_ip`/`abuseipdb` en su día (ver `_omit_none` en
integrity_payloads.py): los casos ya sellados antes de que existieran
deben seguir generando el mismo payload de integridad.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    domain: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    whois: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ssl: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    virustotal: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    abuseipdb: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dns: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_reputations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    crtsh: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    wayback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
