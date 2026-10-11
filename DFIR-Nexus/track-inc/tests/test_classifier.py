from agent.classifier.engine import ClassifierEngine
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")


def test_log_deletion_is_critical():
    engine = ClassifierEngine()
    event = RawEvent(
        source=EventSource.FILESYSTEM,
        event_type="deleted",
        host_info=HOST,
        payload={"path": "/var/log/auth.log"},
    )
    criticality, rule = engine.classify(event)
    assert criticality == Criticality.CRITICAL
    assert rule == "borrado_de_logs"


def test_exec_from_tmp_is_high():
    engine = ClassifierEngine()
    event = RawEvent(
        source=EventSource.PROCESS,
        event_type="exec",
        host_info=HOST,
        payload={"path": "/tmp/payload.sh"},
    )
    criticality, rule = engine.classify(event)
    assert criticality == Criticality.HIGH
    assert rule == "ejecucion_desde_temporal"


def test_unmatched_event_defaults_to_low():
    engine = ClassifierEngine()
    event = RawEvent(
        source=EventSource.FILESYSTEM,
        event_type="modified",
        host_info=HOST,
        payload={"path": "/home/user/notes.txt"},
    )
    criticality, rule = engine.classify(event)
    assert criticality == Criticality.LOW
    assert rule is None


def test_flagged_network_connection_is_high():
    engine = ClassifierEngine()
    event = RawEvent(
        source=EventSource.NETWORK,
        event_type="connection",
        host_info=HOST,
        payload={"remote_ip": "203.0.113.9", "flagged": True},
    )
    criticality, rule = engine.classify(event)
    assert criticality == Criticality.HIGH
    assert rule == "conexion_saliente_sospechosa"
