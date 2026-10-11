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
    # "osint_domain_cases", no "cases": evita colisionar con la tabla
    # `cases` de Nexus (Módulo 1, casos de investigación) — son conceptos
    # distintos (un caso de investigación vs. un análisis de dominio).
    __tablename__ = "osint_domain_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    # Referencia LÓGICA (no FK física) al futuro `cases.id` de Nexus — esa
    # tabla vive en otra base de datos hasta que los módulos se fusionen de
    # verdad. Mismo patrón que `timeline_events.origen_id` en el CLAUDE.md
    # de la rama modulo-casos.
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    whois: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ssl: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    virustotal: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
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
