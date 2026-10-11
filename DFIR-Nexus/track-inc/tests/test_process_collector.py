import time
from unittest.mock import MagicMock, patch

from agent.collectors.process import ProcessCollector


def _mock_proc(pid, ppid=1, name="bash", exe="/bin/bash", user="root", cmdline=None):
    proc = MagicMock()
    proc.info = {
        "pid": pid,
        "ppid": ppid,
        "name": name,
        "exe": exe,
        "username": user,
        "cmdline": cmdline or [exe],
    }
    return proc


def test_new_process_emits_exec_event():
    captured = []
    collector = ProcessCollector(on_event=captured.append, agent_id="agent-001", poll_interval=0.05)

    patcher = patch("agent.collectors.process.psutil.process_iter")
    mock_iter = patcher.start()
    try:
        mock_iter.return_value = [_mock_proc(100)]
        collector.start()
        time.sleep(0.02)  # baseline capturado con pid=100 presente

        mock_iter.return_value = [_mock_proc(100), _mock_proc(200, name="malware.sh", exe="/tmp/malware.sh")]
        time.sleep(0.15)  # dar tiempo a un ciclo de polling
    finally:
        collector.stop()
        patcher.stop()

    exec_events = [e for e in captured if e.event_type == "exec"]
    assert len(exec_events) == 1
    assert exec_events[0].payload["pid"] == 200
    assert exec_events[0].payload["path"] == "/tmp/malware.sh"


def test_terminated_process_emits_terminated_event():
    captured = []
    collector = ProcessCollector(on_event=captured.append, agent_id="agent-001", poll_interval=0.05)

    patcher = patch("agent.collectors.process.psutil.process_iter")
    mock_iter = patcher.start()
    try:
        mock_iter.return_value = [_mock_proc(100), _mock_proc(200)]
        collector.start()
        time.sleep(0.02)

        mock_iter.return_value = [_mock_proc(100)]
        time.sleep(0.15)
    finally:
        collector.stop()
        patcher.stop()

    terminated_events = [e for e in captured if e.event_type == "terminated"]
    assert len(terminated_events) == 1
    assert terminated_events[0].payload["pid"] == 200


def test_baseline_does_not_emit_events_for_preexisting_processes():
    """Los procesos que YA estaban corriendo cuando arranca el agente no
    deben generar eventos 'exec' retroactivos, solo los nuevos."""
    captured = []
    collector = ProcessCollector(on_event=captured.append, agent_id="agent-001", poll_interval=0.05)

    patcher = patch("agent.collectors.process.psutil.process_iter")
    mock_iter = patcher.start()
    try:
        mock_iter.return_value = [_mock_proc(100), _mock_proc(200)]
        collector.start()
        time.sleep(0.15)  # incluso tras un ciclo de polling sin cambios
    finally:
        collector.stop()
        patcher.stop()

    assert len(captured) == 0
