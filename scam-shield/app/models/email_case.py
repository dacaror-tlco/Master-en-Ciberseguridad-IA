"""
Modelo de base de datos para un caso de análisis de email.

Igual que con Case (dominios): guardamos el detalle como JSON para poder
iterar rápido en la fase 1-2 sin migraciones constantes. No guardamos el
raw_email completo por defecto (puede contener datos personales sensibles
del remitente/víctima); solo lo extraído. Si más adelante hace falta
conservar el original como prueba, lo añadiremos como campo explícito y
cifrado, no en claro.

`raw_email_sha256`: huella del email ORIGINAL en el momento de la
captura. Es solo informativa (para que el usuario pueda comparar su
.eml si lo conserva él) — NO participa en la cadena de custodia
verificable (integrity_service.py), porque al no guardar el contenido
original no hay forma de recalcularla más adelante para comprobarla, y
eso generaría falsos positivos de "manipulación" que no existen.

`links`, `attachments`, `is_raw_source`, `ai_explanation` y
`originating_ip_abuseipdb` se añadieron después de los campos
originales — son nullable / con default para que los casos ya sellados
antes de que existieran sigan generando el mismo payload de integridad
(ver `_omit_none` en integrity_payloads.py).
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmailCase(Base):
    __tablename__ = "email_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_address: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer)

    headers: Mapped[dict] = mapped_column(JSON)
    sender_domain_whois: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    originating_ip_abuseipdb: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    attachments: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_raw_source: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    raw_email_sha256: Mapped[str | None] = mapped_column(String, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

