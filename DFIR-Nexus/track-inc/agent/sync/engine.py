"""
Sync Engine: toma las evidencias `pending` del store local y las envía al
servidor central en lotes, con reintentos y backoff exponencial. No
pierde evidencias si el servidor no está disponible: simplemente se
quedan `pending` hasta el siguiente intento.
"""

from __future__ import annotations

import logging
import time

from agent.evidence.store import EvidenceStore

from .transport import EvidenceTransport

logger = logging.getLogger(__name__)


class SyncEngine:
    def __init__(
        self,
        store: EvidenceStore,
        transport: EvidenceTransport,
        batch_size: int = 50,
        max_retries: int = 5,
        base_backoff_seconds: float = 1.0,
    ):
        self.store = store
        self.transport = transport
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds

    def sync_once(self) -> int:
        """Intenta enviar un único lote de pendientes. Devuelve cuántos se
        confirmaron (acked). No bloquea: si falla, deja los registros
        como pending y retorna 0 (se reintentará en la siguiente pasada)."""
        pending = self.store.get_pending(limit=self.batch_size)
        if not pending:
            return 0

        result = self._send_with_retries(pending)
        if result is None:
            logger.warning("Sync fallido tras %s reintentos; %s evidencias siguen pending", self.max_retries, len(pending))
            return 0

        for record_id in result.accepted_ids:
            self.store.mark_synced(record_id, status="acked")

        if result.rejected_ids:
            logger.error("El servidor rechazó %s evidencias: %s", len(result.rejected_ids), result.rejected_ids)

        return len(result.accepted_ids)

    def run_forever(self, interval_seconds: float = 5.0, stop_flag=lambda: False) -> None:
        """Bucle simple para el servicio de sistema. `stop_flag` es un
        callable que, si devuelve True, detiene el bucle (para tests /
        apagado ordenado)."""
        while not stop_flag():
            self.sync_once()
            time.sleep(interval_seconds)

    def _send_with_retries(self, records):
        for attempt in range(self.max_retries):
            result = self.transport.send_batch(records)
            if result.ok:
                return result
            backoff = self.base_backoff_seconds * (2 ** attempt)
            logger.info("Intento %s/%s fallido (%s); reintentando en %.1fs", attempt + 1, self.max_retries, result.error, backoff)
            time.sleep(backoff)
        return None
