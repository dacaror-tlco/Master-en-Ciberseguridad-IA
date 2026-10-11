"""
Demo end-to-end CON monitorización real de filesystem (no eventos
simulados): crea una carpeta temporal, arranca el FilesystemCollector de
verdad sobre ella, provoca unos cuantos cambios (crear/modificar/borrar
ficheros) y observa cómo el pipeline completo los captura, clasifica,
encadena y "sincroniza" (con un transporte mock).

Ejecutar con:
    python -m examples.demo_end_to_end
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from agent.classifier.engine import ClassifierEngine
from agent.collectors.filesystem import FilesystemCollector
from agent.evidence.chain import EvidenceChain, verify_chain
from agent.evidence.store import EvidenceStore
from agent.sync.engine import SyncEngine
from agent.sync.mock_transport import MockEvidenceTransport


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        watch_dir = Path(tmp) / "watched"
        watch_dir.mkdir()
        db_path = Path(tmp) / "evidence.db"

        classifier = ClassifierEngine()
        chain = EvidenceChain()
        store = EvidenceStore(db_path)

        captured = []

        def on_event(raw_event):
            criticality, rule = classifier.classify(raw_event)
            record = chain.append(raw_event, criticality, matched_rule=rule)
            store.append(record)
            captured.append(record)
            print(f"[capturado] {raw_event.event_type:<10} {raw_event.payload.get('path')} -> {criticality.value}")

        collector = FilesystemCollector(
            on_event=on_event,
            watch_paths=[str(watch_dir)],
            agent_id="agent-demo-fs",
        )

        print(f"Monitorizando: {watch_dir}\n")
        collector.start()
        time.sleep(0.3)  # dar tiempo al observer a arrancar del todo

        # Provocamos actividad real en el filesystem
        f1 = watch_dir / "documento.txt"
        f1.write_text("contenido inicial")
        time.sleep(0.3)

        f1.write_text("contenido modificado")
        time.sleep(0.3)

        f1.unlink()
        time.sleep(0.5)  # dar tiempo a que lleguen los eventos async

        collector.stop()

        print(f"\nTotal de eventos capturados: {len(captured)}")

        all_records = store.get_all()
        verify_chain(all_records)
        print(f"✔ Cadena de {len(all_records)} evidencias verificada.")

        # Ahora sincronizamos con un servidor "mock"
        transport = MockEvidenceTransport()
        sync_engine = SyncEngine(store, transport)
        synced = sync_engine.sync_once()
        print(f"✔ {synced} evidencias sincronizadas con el servidor (simulado).")
        print(f"Pendientes tras sync: {len(store.get_pending())}")

        store.close()


if __name__ == "__main__":
    main()
