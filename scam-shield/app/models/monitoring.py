"""
Monitorización continua de los sujetos ya analizados (dominios, wallets,
teléfonos, dominios protegidos frente a typosquatting, búsquedas CNMV).

Cada sujeto (case_type + identifier) se re-analiza periódicamente
reutilizando exactamente el mismo pipeline que el análisis manual (mismo
servicio, mismo risk_engine, mismo registro en la cadena de custodia) —
cada re-chequeo crea un CASO NUEVO, nunca modifica uno existente, para no
romper la cadena de integridad (ver integrity_service.py). MonitoredSubject
solo guarda el "estado de seguimiento" (¿está activo?, ¿cuándo se
comprobó por última vez?, ¿cuál fue el último score?) para saber cuándo
re-chequear y para poder comparar contra el resultado anterior.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MonitoredSubject(Base):
    __tablename__ = "monitored_subjects"
    __table_args__ = (UniqueConstraint("case_type", "identifier", name="uq_monitored_subject"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_type: Mapped[str] = mapped_column(String, index=True)  # domain | wallet | phone | typosquatting | cnmv
    identifier: Mapped[str] = mapped_column(String, index=True)  # dominio, dirección, e164, query normalizada...

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    check_interval_hours: Mapped[int] = mapped_column(Integer, default=24)

    last_case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_bucket: Mapped[str | None] = mapped_column(String, nullable=True)  # low | medium | high
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    case_type: Mapped[str] = mapped_column(String, index=True)
    identifier: Mapped[str] = mapped_column(String, index=True)

    previous_case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_bucket: Mapped[str | None] = mapped_column(String, nullable=True)
    new_case_id: Mapped[int] = mapped_column(Integer)
    new_score: Mapped[int] = mapped_column(Integer)
    new_bucket: Mapped[str] = mapped_column(String)

    reason: Mapped[str] = mapped_column(String)  # texto legible: por qué se generó la alerta
    new_flag_codes: Mapped[list] = mapped_column(JSON, default=list)

    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
