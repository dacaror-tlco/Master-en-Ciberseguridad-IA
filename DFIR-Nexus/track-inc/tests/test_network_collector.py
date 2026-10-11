import time
from unittest.mock import MagicMock, patch

from agent.collectors.network import NetworkCollector


def _mock_conn(pid, remote_ip, remote_port=443, local_port=51000, status="ESTABLISHED"):
    conn = MagicMock()
    conn.pid = pid
    conn.status = status
    conn.laddr = MagicMock(ip="10.0.0.5", port=local_port)
    conn.raddr = MagicMock(ip=remote_ip, port=remote_port)
    return conn


def test_new_connection_emits_event():
    captured = []
    collector = NetworkCollector(on_event=captured.append, agent_id="agent-001", poll_interval=0.05)

    patcher = patch("agent.collectors.network.psutil.net_connections")
    mock_conns = patcher.start()
    try:
        mock_conns.return_value = []
        collector.start()
        time.sleep(0.02)

        mock_conns.return_value = [_mock_conn(pid=500, remote_ip="93.184.216.34")]
        time.sleep(0.15)
    finally:
        collector.stop()
        patcher.stop()

    assert len(captured) == 1
    assert captured[0].payload["remote_ip"] == "93.184.216.34"
    assert captured[0].payload["flagged"] is False


def test_blacklisted_ip_is_flagged():
    captured = []
    collector = NetworkCollector(
        on_event=captured.append,
        agent_id="agent-001",
        poll_interval=0.05,
        ip_blacklist={"203.0.113.55"},
    )

    patcher = patch("agent.collectors.network.psutil.net_connections")
    mock_conns = patcher.start()
    try:
        mock_conns.return_value = []
        collector.start()
        time.sleep(0.02)

        mock_conns.return_value = [_mock_conn(pid=500, remote_ip="203.0.113.55", remote_port=4444)]
        time.sleep(0.15)
    finally:
        collector.stop()
        patcher.stop()

    assert len(captured) == 1
    assert captured[0].payload["flagged"] is True
    assert captured[0].payload["remote_ip"] == "203.0.113.55"
