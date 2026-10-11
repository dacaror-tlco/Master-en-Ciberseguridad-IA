"""
`osint_findings` — modelo de LECTURA que scam-shield publica para el resto
de módulos de Nexus (tracking, informes, timeline...).

Por qué existe (ver docs/CONTRATO-DATOS.md):

- Cada sub-módulo de OSINT guarda su caso en su propia tabla
  (`osint_domain_cases`, `email_cases`, `wallet_cases`...), con columnas
  distintas cada una. Un consumidor que quisiera "todo lo analizado con
  riesgo alto de esta semana" tendría que conocer y unir 10 tablas
  internas y su lógica de scoring.
- `osint_findings` es una fila desnormalizada por análisis terminado, con
  un esquema ESTABLE y común: tipo, sujeto, score, nivel, titular, flags
  y el payload completo en `details`. Los otros módulos leen SOLO de aquí
  (+ `cases` de Nexus), nunca de las tablas internas.
- Es un contrato: solo se le añaden columnas, nunca se le quitan ni se
  renombran. Si hiciera falta romperlo, se crea `osint_findings_v2`.

Se rellena en `findings/service.py::record_finding`, llamado justo después
de sellar cada caso en la cadena de integridad (mismo sitio, en cada
`*/service.py`). Es un proyección: si su escritura falla, el análisis en
sí NO falla (ver record_finding).
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OsintFinding(Base):
    __tablename__ = "osint_findings"
    __table_args__ = (
        # Los casos son append-only (un re-análisis crea una fila nueva en la
        # tabla de origen), así que cada (case_type, source_id) genera como
        # mucho un finding. La restricción es una red de seguridad.
        UniqueConstraint("case_type", "source_id", name="uq_osint_finding_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # --- de qué análisis viene ---
    # Vocabulario de case_type, el MISMO que integrity_ledger / monitoring:
    # domain | email | wallet | typosquatting | phone | cnmv | ip | image |
    # image_reverse_search | image_facial_search
    case_type: Mapped[str] = mapped_column(String(32), index=True)
    source_table: Mapped[str] = mapped_column(String(64))  # tabla interna real (osint_domain_cases, ...)
    source_id: Mapped[int] = mapped_column(Integer, index=True)  # PK en esa tabla

    # Referencia LÓGICA (no FK física) al `cases.id` de Nexus (Módulo 1).
    # NULL mientras el análisis no esté atado a un expediente formal — ver
    # CONTRATO-DATOS.md ("Cómo se rellena case_id").
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # --- sobre qué se analizó (normalizado) ---
    # subject_type: domain | email_address | crypto_wallet | ip_address |
    # phone_number | entity_name | image_file
    subject_type: Mapped[str] = mapped_column(String(32), index=True)
    subject_value: Mapped[str] = mapped_column(String(255), index=True)  # el identificador (dominio, dirección, IP...)

    # --- veredicto ---
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    risk_level: Mapped[str] = mapped_column(String(16), index=True)  # low | medium | high (shared/risk_levels.py)
    headline: Mapped[str] = mapped_column(String(255))  # resumen de una línea, listo para pintar
    flag_count: Mapped[int] = mapped_column(Integer, default=0)
    top_flags: Mapped[list] = mapped_column(JSON, default=list)  # [{code, severity, description}], recortado
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # payload completo del caso (integrity_payloads)

    # --- tiempos ---
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)  # cuándo se hizo el análisis
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
