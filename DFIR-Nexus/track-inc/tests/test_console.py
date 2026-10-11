import pytest

from agent.classifier.engine import ClassifierEngine
from agent.config import AgentConfig
from agent.console.app import create_app
from agent.evidence.chain import EvidenceChain
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent
from agent.evidence.store import EvidenceStore

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")


@pytest.fixture
def app_client(tmp_path):
    watch_dir = tmp_path / "watched"
    watch_dir.mkdir()
    db_path = tmp_path / "evidence.db"

    # seed con un par de evidencias de distintas criticidades/orígenes
    classifier = ClassifierEngine()
    chain = EvidenceChain()
    store = EvidenceStore(db_path)
    events = [
        RawEvent(source=EventSource.FILESYSTEM, event_type="deleted", host_info=HOST, payload={"path": "/var/log/auth.log"}),
        RawEvent(source=EventSource.NETWORK, event_type="connection", host_info=HOST, payload={"remote_ip": "1.2.3.4", "flagged": True}),
    ]
    for e in events:
        crit, rule = classifier.classify(e)
        store.append(chain.append(e, crit, matched_rule=rule))
    store.close()

    config = AgentConfig.model_validate({
        "agent_id": "agent-test",
        "db_path": str(db_path),
        "rules_path": "agent/classifier/rules.yaml",
        "collectors": {"watch_paths": [str(watch_dir)]},
        "sync": {"server_url": None},
    })
    app = create_app(config)
    app.config["TESTING"] = True
    return app.test_client()


def test_dashboard_shows_correct_counts(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "agent-test" in body
    assert "2" in body  # total de evidencias


def test_evidence_list_shows_records(app_client):
    response = app_client.get("/evidence")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "auth.log" in body
    assert "CRITICAL" in body


def test_evidence_list_filters_by_criticality(app_client):
    response = app_client.get("/evidence?criticality=CRITICAL")
    body = response.get_data(as_text=True)
    assert "auth.log" in body
    assert "1.2.3.4" not in body  # el evento de red (HIGH) no debe aparecer


def test_evidence_list_filters_by_source(app_client):
    response = app_client.get("/evidence?source=network")
    body = response.get_data(as_text=True)
    assert "1.2.3.4" in body
    assert "auth.log" not in body


def test_verify_endpoint_reports_success_for_intact_chain(app_client):
    response = app_client.post("/verify", follow_redirects=True)
    assert response.status_code == 200
    assert "íntegra" in response.get_data(as_text=True)


def test_sync_endpoint_syncs_pending_evidence(app_client):
    response = app_client.post("/sync", follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "sincronizadas correctamente" in body

    # una segunda sincronización no debería tener nada pendiente
    response2 = app_client.post("/sync", follow_redirects=True)
    assert "No había evidencias pendientes" in response2.get_data(as_text=True)


def test_rules_page_lists_active_rules(app_client):
    response = app_client.get("/rules")
    assert response.status_code == 200
    assert "borrado_de_logs" in response.get_data(as_text=True)


def test_config_page_hides_api_key(app_client):
    response = app_client.get("/config")
    assert response.status_code == 200
    assert "agent-test" in response.get_data(as_text=True)
