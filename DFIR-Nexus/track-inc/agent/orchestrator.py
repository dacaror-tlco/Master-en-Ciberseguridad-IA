"""
Orquestador del agente. Es la pieza que el servicio de sistema (systemd /
Windows Service / launchd) arranca y para. Responsabilidades:

  1. Construir todos los componentes a partir de AgentConfig.
  2. Reanudar la cadena de hashes desde el último estado conocido en el
     store local (si el agente se reinició).
  3. Arrancar los collectors habilitados, todos apuntando al mismo
     pipeline (clasificar -> encadenar -> guardar).
  4. Correr el Sync Engine en un hilo de fondo, a intervalos regulares.
  5. Parar todo de forma ordenada (para apagados limpios, no solo kills).
"""

from __future__ import annotations

import logging
import threading

from agent.classifier.engine import ClassifierEngine
from agent.collectors.base import Collector
from agent.collectors.filesystem import FilesystemCollector
from agent.collectors.network import NetworkCollector
from agent.collectors.process import ProcessCollector
from agent.config import AgentConfig
from agent.evidence.chain import EvidenceChain
from agent.evidence.models import Criticality, RawEvent
from agent.evidence.store import EvidenceStore
from agent.sync.engine import SyncEngine
from agent.sync.http_transport import HttpEvidenceTransport
from agent.sync.mock_transport import MockEvidenceTransport
from agent.sync.transport import EvidenceTransport

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, config: AgentConfig):
        self.config = config

        self.store = EvidenceStore(config.db_path)
        self.classifier = ClassifierEngine.from_yaml(config.rules_path)

        last_hash, last_seq = self.store.get_last_hash_and_seq()
        self.chain = EvidenceChain(last_hash=last_hash, last_seq=last_seq)
        logger.info("Cadena reanudada: seq=%s, hash=%s...", last_seq, last_hash[:12])

        self.transport = self._build_transport(config)
        self.sync_engine = SyncEngine(
            self.store, self.transport,
            batch_size=config.sync.batch_size,
            max_retries=config.sync.max_retries,
        )

        self.collectors: list[Collector] = self._build_collectors(config)
        self._sync_thread: threading.Thread | None = None
        self._stop_sync = threading.Event()

    # -- construcción ----------------------------------------------------

    @staticmethod
    def _build_transport(config: AgentConfig) -> EvidenceTransport:
        if config.sync.server_url:
            return HttpEvidenceTransport(
                base_url=config.sync.server_url,
                agent_id=config.agent_id,
                api_key=config.sync.api_key,
            )
        logger.warning("No hay server_url configurada: usando transporte MOCK (nada se envía de verdad).")
        return MockEvidenceTransport()

    def _build_collectors(self, config: AgentConfig) -> list[Collector]:
        collectors: list[Collector] = []
        c = config.collectors

        if c.filesystem_enabled:
            collectors.append(FilesystemCollector(
                on_event=self._on_event,
                watch_paths=c.watch_paths,
                agent_id=config.agent_id,
            ))
        if c.process_enabled:
            collectors.append(ProcessCollector(
                on_event=self._on_event,
                agent_id=config.agent_id,
                poll_interval=c.process_poll_interval,
            ))
        if c.network_enabled:
            collectors.append(NetworkCollector(
                on_event=self._on_event,
                agent_id=config.agent_id,
                poll_interval=c.network_poll_interval,
                ip_blacklist=set(c.ip_blacklist),
            ))
        return collectors

    # -- pipeline ----------------------------------------------------------

    def _on_event(self, event: RawEvent) -> None:
        criticality, rule = self.classifier.classify(event)
        record = self.chain.append(event, criticality, matched_rule=rule)
        self.store.append(record)
        logger.debug("Evidencia seq=%s %s/%s -> %s (regla=%s)", record.seq, event.source.value, event.event_type, criticality.value, rule)

    # -- ciclo de vida -------------------------------------------------------

    def start(self) -> None:
        logger.info("Arrancando %s collectors...", len(self.collectors))
        for collector in self.collectors:
            collector.start()
            logger.info("Collector '%s' arrancado.", collector.name)

        self._stop_sync.clear()
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info("Sync engine arrancado (intervalo=%ss).", self.config.sync.interval_seconds)

    def stop(self) -> None:
        logger.info("Deteniendo orquestador...")
        for collector in self.collectors:
            collector.stop()
            logger.info("Collector '%s' detenido.", collector.name)

        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=self.config.sync.interval_seconds + 5)

        # último intento de vaciar la cola antes de cerrar, para no dejar
        # evidencias pendientes más tiempo del necesario
        self.sync_engine.sync_once()
        self.store.close()
        logger.info("Orquestador detenido de forma ordenada.")

    def _sync_loop(self) -> None:
        while not self._stop_sync.is_set():
            try:
                self.sync_engine.sync_once()
            except Exception:
                logger.exception("Error inesperado en el ciclo de sincronización")
            self._stop_sync.wait(self.config.sync.interval_seconds)
