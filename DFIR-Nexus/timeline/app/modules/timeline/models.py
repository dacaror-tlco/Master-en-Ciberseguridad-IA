"""
Modelo de `timeline_events` (Módulo 4), propiedad exclusiva de este
backend. FK real a `cases.id` con `ON DELETE CASCADE` — así está ya
confirmado en Aiven (04/09/2026), y así se declara aquí para que quien
levante este backend contra una base nueva obtenga la misma estructura.

Índice compuesto (origen_modulo, origen_id) añadido respecto a la versión
de origen (`feature/timeline-integration`): CLAUDE.md lo exige para este
módulo y faltaba — es una adición aditiva sobre una tabla que este mismo
backend posee y crea, no una migración sobre tablas ajenas.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.core.database import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("ix_timeline_events_origen", "origen_modulo", "origen_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    descripcion = Column(Text, nullable=False)
    # Referencia LÓGICA, no FK física (CLAUDE.md): apunta a evidences,
    # osint_findings o tracking_events según origen_modulo. Resuelta a
    # nivel de aplicación, nunca con una constraint de base de datos.
    origen_modulo = Column(String(30), nullable=False)
    origen_id = Column(Integer, nullable=False)
    orden = Column(Integer, nullable=False)
