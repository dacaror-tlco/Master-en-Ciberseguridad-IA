"""
Modelos de datos del Módulo 3 (Agente de Adquisición de Evidencias).

RawEvent      -> lo que emite un collector (fs, proceso, red) sin procesar.
Criticality   -> nivel asignado por el clasificador.
EvidenceRecord-> un RawEvent ya clasificado y enlazado dentro de la cadena
                 de hashes (chain of custody digital).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    FILESYSTEM = "filesystem"
    PROCESS = "process"
    NETWORK = "network"
    LOG = "log"  # eventos extraídos de un fichero de log ya existente (CU-03),
                 # a diferencia de FILESYSTEM/PROCESS/NETWORK que vienen de
                 # monitorización en vivo


class Criticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HostInfo(BaseModel):
    agent_id: str
    hostname: str
    os: str  # "linux" | "windows" | "darwin"


class RawEvent(BaseModel):
    """Evento crudo tal como lo produce un collector, ya normalizado."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: EventSource
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    host_info: HostInfo
    payload: dict

    def canonical_dict(self) -> dict:
        """Representación determinista (para hashear), sin depender del
        orden de inserción de los campos."""
        return {
            "id": self.id,
            "source": self.source.value,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "host_info": self.host_info.model_dump(),
            "payload": self.payload,
        }


class EvidenceRecord(BaseModel):
    """Un RawEvent clasificado y anclado en la cadena de hashes."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event: RawEvent
    criticality: Criticality
    matched_rule: str | None = None  # qué regla del clasificador disparó esto
    seq: int  # posición dentro de la cadena local (0, 1, 2, ...)
    prev_hash: str
    hash: str

    # estado de sincronización con el servidor central
    sync_status: str = "pending"  # pending | sent | acked

    def canonical_payload_for_hash(self) -> dict:
        """Lo que se hashea NO incluye el propio hash (obviamente) ni el
        sync_status, porque ese cambia después y no debe romper la cadena."""
        return {
            "id": self.id,
            "event": self.event.canonical_dict(),
            "criticality": self.criticality.value,
            "matched_rule": self.matched_rule,
            "seq": self.seq,
            "prev_hash": self.prev_hash,
        }
