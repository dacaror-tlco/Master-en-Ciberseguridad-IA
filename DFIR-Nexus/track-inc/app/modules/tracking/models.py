"""
Modelo oficial de `tracking_events` (Módulo 3), según CLAUDE.md.

Importante: este modelo NO contiene ningún campo relacionado con la
cadena de hashes/integridad. Esa capa existe (ver
`app/modules/tracking/chain_integrity.py`) pero vive
deliberadamente fuera de este esquema — es una decisión explícita para
no anticipar en el modelo de datos oficial algo que CLAUDE.md marca
como "fuera de alcance por ahora". Ver ese fichero para más contexto.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, Table
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: Referencia local a `cases`, que es del Módulo 1.
#:
#: `tracking_events.case_id` tiene FK física a `cases.id`, y SQLAlchemy necesita
#: encontrar la tabla apuntada **dentro de este `MetaData`** para ordenar las
#: tablas al hacer `flush`. Sin ella, cualquier INSERT en `tracking_events`
#: aborta con `NoReferencedTableError` y el endpoint de guardado responde 500.
#: El fallo no se veía en los tests porque su `conftest` declara una `cases` de
#: apoyo, que es justo lo que faltaba con la aplicación en marcha: se retiró el
#: modelo placeholder de Casos al integrar en `development` —y `case_exists`
#: pasó a leer con SQL directo, ver `repository.py`— pero la FK del modelo
#: siguió necesitando un destino que resolver.
#:
#: Se declara como `Table` de Core y solo con la clave primaria, no como modelo:
#: `docs/CONTRATOS.md` exige que quien lee una tabla ajena declare su propia
#: referencia y **nunca importe el modelo ORM del dueño**. Tracking no la lee ni
#: la escribe por aquí; solo necesita saber que existe. El cortafuegos
#: `include_object` de `alembic/env.py` la deja fuera de las migraciones de este
#: backend, que solo gestiona `tracking_events`.
Table("cases", Base.metadata, Column("id", Integer, primary_key=True))


class Severidad(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    __table_args__ = (
        Index("ix_tracking_events_case_id", "case_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    hora: Mapped[datetime] = mapped_column(nullable=False)
    evento: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[Severidad] = mapped_column(
        SAEnum(Severidad, name="severidad_tracking", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    fuente_log: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usuario_detectado: Mapped[str | None] = mapped_column(String(100), nullable=True)
