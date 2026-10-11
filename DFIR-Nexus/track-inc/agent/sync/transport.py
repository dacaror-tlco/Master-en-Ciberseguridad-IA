"""
Interfaz de transporte hacia el servidor central. Se define como
Protocol para que el Sync Engine no dependa de ninguna implementación
concreta -> cuando el equipo defina la API real, solo hay que escribir
una nueva clase que cumpla este contrato (o ajustar HttpEvidenceTransport).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from agent.evidence.models import EvidenceRecord


@dataclass
class SyncResult:
    accepted_ids: list[str] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class EvidenceTransport(Protocol):
    def send_batch(self, records: list[EvidenceRecord]) -> SyncResult:
        """Envía un lote de evidencias. Debe ser idempotente: reenviar un
        record.id ya aceptado por el servidor no debe duplicarlo."""
        ...

    def health_check(self) -> bool:
        """True si el servidor central es alcanzable ahora mismo."""
        ...

    def get_last_hash(self, agent_id: str) -> str | None:
        """Último hash conocido por el servidor para este agente (para
        poder reanudar la cadena si el store local se perdiera). None si
        el servidor no tiene nada registrado aún."""
        ...
