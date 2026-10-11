import time
from unittest.mock import patch

import pytest

from agent.config import AgentConfig
from agent.evidence.chain import verify_chain
from agent.evidence.store import EvidenceStore
from agent.orchestrator import Orchestrator
from agent.sync.mock_transport import MockEvidenceTransport


def make_config(tmp_path, **overrides) -> AgentConfig:
    watch_dir = tmp_path / "watched"
    watch_dir.mkdir()
    base = {
        "agent_id": "agent-test",
        "db_path": str(tmp_path / "evidence.db"),
        "rules_path": "agent/classifier/rules.yaml",
        "collectors": {
            "filesystem_enabled": True,
            "watch_paths": [str(watch_dir)],
            "process_enabled": False,   # desactivados para tests deterministas
            "network_enabled": False,
        },
        "sync": {
            "server_url": None,  # -> usa MockEvidenceTransport
            "interval_seconds": 0.1,
        },
    }
    base.update(overrides)
    return AgentConfig.model_validate(base), watch_dir


def test_orchestrator_builds_from_config_without_server_url(tmp_path):
    """Sin server_url configurada, debe usar el transporte mock en vez de
    fallar o intentar conectar a ningún sitio."""
    config, _ = make_config(tmp_path)
    orchestrator = Orchestrator(config)

    assert isinstance(orchestrator.transport, MockEvidenceTransport)
    assert len(orchestrator.collectors) == 1  # solo filesystem, el resto desactivado
    orchestrator.store.close()


def test_orchestrator_resumes_chain_from_existing_store(tmp_path):
    """Si ya había evidencias guardadas de una sesión anterior, el
    orquestador debe reanudar la cadena desde ahí, no desde cero."""
    config, _ = make_config(tmp_path)

    # "sesión 1": escribimos algo directamente al store antes de construir el orquestador
    from agent.evidence.chain import EvidenceChain
    from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent

    store = EvidenceStore(config.db_path)
    chain = EvidenceChain()
    event = RawEvent(source=EventSource.FILESYSTEM, event_type="modified",
                      host_info=HostInfo(agent_id="agent-test", hostname="h", os="linux"),
                      payload={"path": "/tmp/x"})
    store.append(chain.append(event, Criticality.LOW))
    store.close()

    # "sesión 2": el orquestador arranca y debe continuar, no reiniciar
    orchestrator = Orchestrator(config)
    assert orchestrator.chain.last_seq == 0
    assert orchestrator.chain.last_hash == chain.last_hash
    orchestrator.store.close()


def test_orchestrator_pipeline_end_to_end_with_real_filesystem_collector(tmp_path):
    """El test de integración más importante: arrancar de verdad, tocar el
    filesystem real, y comprobar que el evento llega encadenado y
    guardado en el store."""
    config, watch_dir = make_config(tmp_path)
    orchestrator = Orchestrator(config)

    orchestrator.start()
    time.sleep(0.2)

    (watch_dir / "nuevo.txt").write_text("contenido")
    time.sleep(0.4)

    orchestrator.stop()

    # tras stop(), el store del orquestador queda cerrado (apagado ordenado);
    # comprobamos el resultado abriendo una conexión nueva, como haría
    # cualquier proceso externo auditando el fichero después
    audit_store = EvidenceStore(config.db_path)
    all_records = audit_store.get_all()
    assert len(all_records) >= 1
    verify_chain(all_records)
    audit_store.close()


def test_orchestrator_syncs_automatically_in_background(tmp_path):
    """El sync engine debe correr solo, en segundo plano, sin que nadie
    llame a sync_once() manualmente."""
    config, watch_dir = make_config(tmp_path)
    orchestrator = Orchestrator(config)

    orchestrator.start()
    time.sleep(0.15)
    (watch_dir / "archivo.txt").write_text("x")
    time.sleep(0.5)  # varios ciclos de sync (interval_seconds=0.1)

    orchestrator.stop()

    transport = orchestrator.transport
    assert isinstance(transport, MockEvidenceTransport)
    assert len(transport.sent_batches) >= 1  # se sincronizó solo, en background


def test_orchestrator_stops_cleanly_and_flushes_pending(tmp_path):
    """Al parar, debe hacer un último intento de sincronizar lo pendiente
    antes de cerrar, para no dejar evidencias esperando más de lo necesario."""
    config, watch_dir = make_config(tmp_path, sync={"server_url": None, "interval_seconds": 999})  # sync loop lento a propósito
    orchestrator = Orchestrator(config)

    orchestrator.start()
    time.sleep(0.2)
    (watch_dir / "archivo.txt").write_text("x")
    time.sleep(0.3)

    orchestrator.stop()  # con interval_seconds=999, el loop de fondo no habría sincronizado a tiempo

    transport = orchestrator.transport
    assert len(transport.sent_batches) >= 1  # el flush final en stop() lo cubrió
