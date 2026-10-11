from agent.evidence.chain import EvidenceChain
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent
from agent.evidence.store import EvidenceStore
from agent.sync.engine import SyncEngine
from agent.sync.mock_transport import MockEvidenceTransport

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")


def make_event() -> RawEvent:
    return RawEvent(
        source=EventSource.FILESYSTEM,
        event_type="modified",
        host_info=HOST,
        payload={"path": "/etc/hosts"},
    )


def seed_store(store: EvidenceStore, n: int) -> None:
    chain = EvidenceChain()
    for _ in range(n):
        store.append(chain.append(make_event(), Criticality.LOW))


def test_sync_once_sends_all_pending_and_marks_acked(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.db")
    seed_store(store, 3)
    transport = MockEvidenceTransport()
    engine = SyncEngine(store, transport, batch_size=10)

    synced = engine.sync_once()

    assert synced == 3
    assert len(store.get_pending()) == 0
    assert len(transport.sent_batches) == 1
    store.close()


def test_sync_respects_batch_size(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.db")
    seed_store(store, 25)
    transport = MockEvidenceTransport()
    engine = SyncEngine(store, transport, batch_size=10)

    first = engine.sync_once()
    assert first == 10
    assert len(store.get_pending()) == 15

    second = engine.sync_once()
    assert second == 10
    assert len(store.get_pending()) == 5
    store.close()


def test_sync_retries_and_eventually_succeeds(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.db")
    seed_store(store, 2)
    # falla las primeras 2 veces, la 3ª tiene éxito
    transport = MockEvidenceTransport(fail_next_n=2)
    engine = SyncEngine(store, transport, max_retries=5, base_backoff_seconds=0.01)

    synced = engine.sync_once()

    assert synced == 2
    assert len(store.get_pending()) == 0
    store.close()


def test_sync_keeps_pending_if_server_unreachable(tmp_path):
    """Si el servidor no responde nunca, no se pierde ninguna evidencia:
    se quedan `pending` para el siguiente intento."""
    store = EvidenceStore(tmp_path / "evidence.db")
    seed_store(store, 4)
    transport = MockEvidenceTransport(fail_next_n=999)  # siempre falla
    engine = SyncEngine(store, transport, max_retries=3, base_backoff_seconds=0.01)

    synced = engine.sync_once()

    assert synced == 0
    assert len(store.get_pending()) == 4  # nada se perdió
    store.close()


def test_sync_with_no_pending_returns_zero(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.db")
    transport = MockEvidenceTransport()
    engine = SyncEngine(store, transport)

    assert engine.sync_once() == 0
    assert len(transport.sent_batches) == 0
    store.close()
