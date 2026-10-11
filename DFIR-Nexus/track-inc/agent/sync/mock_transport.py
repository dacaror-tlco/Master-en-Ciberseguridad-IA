"""
Transporte simulado, útil para:
  - tests unitarios del Sync Engine sin red real
  - desarrollar/demostrar el agente mientras el servidor central no existe

Permite simular fallos de red (fail_next_n) para probar reintentos.
"""

from __future__ import annotations

from agent.evidence.models import EvidenceRecord

from .transport import SyncResult


class MockEvidenceTransport:
    def __init__(self, fail_next_n: int = 0, reachable: bool = True):
        self.sent_batches: list[list[EvidenceRecord]] = []
        self._fail_next_n = fail_next_n
        self._reachable = reachable

    def send_batch(self, records: list[EvidenceRecord]) -> SyncResult:
        if self._fail_next_n > 0:
            self._fail_next_n -= 1
            return SyncResult(error="simulated network failure")

        self.sent_batches.append(records)
        return SyncResult(accepted_ids=[r.id for r in records])

    def health_check(self) -> bool:
        return self._reachable

    def get_last_hash(self, agent_id: str) -> str | None:
        return None
