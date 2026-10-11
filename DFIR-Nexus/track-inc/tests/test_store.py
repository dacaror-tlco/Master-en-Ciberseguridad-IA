from agent.evidence.chain import GENESIS_HASH, EvidenceChain, verify_chain
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent
from agent.evidence.store import EvidenceStore

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")


def make_event() -> RawEvent:
    return RawEvent(
        source=EventSource.FILESYSTEM,
        event_type="modified",
        host_info=HOST,
        payload={"path": "/etc/hosts"},
    )


def test_store_persists_and_reads_back(tmp_path):
    db_path = tmp_path / "evidence.db"
    store = EvidenceStore(db_path)

    chain = EvidenceChain()
    for _ in range(3):
        record = chain.append(make_event(), Criticality.MEDIUM)
        store.append(record)

    all_records = store.get_all()
    assert len(all_records) == 3
    verify_chain(all_records)  # lo leído de disco sigue siendo íntegro
    store.close()


def test_store_resumes_chain_after_restart(tmp_path):
    db_path = tmp_path / "evidence.db"

    # "sesión 1" del agente
    store1 = EvidenceStore(db_path)
    chain1 = EvidenceChain()
    for _ in range(2):
        store1.append(chain1.append(make_event(), Criticality.LOW))
    store1.close()

    # "reinicio del agente" -> nueva conexión al mismo fichero
    store2 = EvidenceStore(db_path)
    last_hash, last_seq = store2.get_last_hash_and_seq()
    assert last_seq == 1
    assert last_hash != GENESIS_HASH

    chain2 = EvidenceChain(last_hash=last_hash, last_seq=last_seq)
    for _ in range(2):
        store2.append(chain2.append(make_event(), Criticality.LOW))

    full = store2.get_all()
    assert [r.seq for r in full] == [0, 1, 2, 3]
    verify_chain(full)
    store2.close()


def test_pending_and_mark_synced(tmp_path):
    db_path = tmp_path / "evidence.db"
    store = EvidenceStore(db_path)
    chain = EvidenceChain()

    r0 = chain.append(make_event(), Criticality.LOW)
    r1 = chain.append(make_event(), Criticality.LOW)
    store.append(r0)
    store.append(r1)

    pending = store.get_pending()
    assert len(pending) == 2

    store.mark_synced(r0.id)
    pending_after = store.get_pending()
    assert len(pending_after) == 1
    assert pending_after[0].id == r1.id
    store.close()
