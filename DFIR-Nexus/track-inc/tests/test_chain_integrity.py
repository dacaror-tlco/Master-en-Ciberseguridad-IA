"""
Tests del núcleo de integridad forense: si estos tests pasan, tenemos
garantía de que cualquier manipulación de una evidencia ya guardada
será detectada.
"""

import pytest

from agent.evidence.chain import ChainError, EvidenceChain, verify_chain
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")


def make_event(event_type="modified", path="/etc/passwd") -> RawEvent:
    return RawEvent(
        source=EventSource.FILESYSTEM,
        event_type=event_type,
        host_info=HOST,
        payload={"path": path},
    )


def test_chain_verifies_when_untouched():
    chain = EvidenceChain()
    records = [chain.append(make_event(), Criticality.MEDIUM) for _ in range(5)]

    verify_chain(records)  # no debe lanzar nada


def test_chain_links_correctly():
    chain = EvidenceChain()
    r0 = chain.append(make_event(), Criticality.LOW)
    r1 = chain.append(make_event(), Criticality.LOW)

    assert r1.prev_hash == r0.hash
    assert r0.seq == 0
    assert r1.seq == 1


def test_tampering_with_payload_breaks_chain():
    """Si alguien modifica el contenido de un evento ya guardado, la
    verificación debe detectarlo."""
    chain = EvidenceChain()
    records = [chain.append(make_event(), Criticality.MEDIUM) for _ in range(3)]

    # Manipulamos el payload del registro del medio, DESPUÉS de calculado el hash
    records[1].event.payload["path"] = "/etc/shadow"

    with pytest.raises(ChainError, match="Hash inválido"):
        verify_chain(records)


def test_reordering_breaks_chain():
    chain = EvidenceChain()
    records = [chain.append(make_event(), Criticality.LOW) for _ in range(4)]

    reordered = [records[0], records[2], records[1], records[3]]

    with pytest.raises(ChainError):
        verify_chain(reordered)


def test_missing_record_breaks_chain():
    """Si se elimina un eslabón intermedio (p. ej. alguien borra una fila
    de la base de datos), debe detectarse el hueco."""
    chain = EvidenceChain()
    records = [chain.append(make_event(), Criticality.LOW) for _ in range(4)]

    with_gap = [records[0], records[1], records[3]]  # falta seq=2

    with pytest.raises(ChainError):
        verify_chain(with_gap)


def test_chain_can_resume_after_restart():
    """Simula un reinicio del agente: se crea una nueva instancia de
    EvidenceChain partiendo del último hash/seq conocido (como si viniera
    de leer el store local), y la cadena resultante sigue siendo válida
    en conjunto."""
    chain_before_restart = EvidenceChain()
    first_batch = [chain_before_restart.append(make_event(), Criticality.LOW) for _ in range(2)]

    # "reinicio": nueva instancia, reanudando desde el último estado conocido
    chain_after_restart = EvidenceChain(
        last_hash=chain_before_restart.last_hash,
        last_seq=chain_before_restart.last_seq,
    )
    second_batch = [chain_after_restart.append(make_event(), Criticality.LOW) for _ in range(2)]

    full_chain = first_batch + second_batch
    assert [r.seq for r in full_chain] == [0, 1, 2, 3]
    verify_chain(full_chain)
