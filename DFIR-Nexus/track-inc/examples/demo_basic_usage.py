"""
Demo ejecutable de los componentes ya implementados del Módulo 3.

Ejecutar con:
    python -m examples.demo_basic_usage
(desde la raíz del proyecto)

Casos de uso cubiertos:
  1. Flujo normal: evento -> clasificación -> cadena -> almacenamiento.
  2. Detección de manipulación (alguien edita una evidencia ya guardada).
  3. Reanudación de la cadena tras un "reinicio" del agente.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent.classifier.engine import ClassifierEngine
from agent.evidence.chain import ChainError, EvidenceChain, verify_chain
from agent.evidence.models import EventSource, HostInfo, RawEvent
from agent.evidence.store import EvidenceStore

HOST = HostInfo(agent_id="agent-demo-001", hostname="workstation-07", os="linux")


def section(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def caso_1_flujo_normal(db_path: Path) -> None:
    section("CASO 1 — Flujo normal: eventos reales -> evidencias encadenadas")

    classifier = ClassifierEngine()
    chain = EvidenceChain()
    store = EvidenceStore(db_path)

    # Simulamos una pequeña secuencia de eventos "capturados" por los
    # collectors, como si fueran parte de un incidente real
    eventos_simulados = [
        RawEvent(source=EventSource.FILESYSTEM, event_type="created", host_info=HOST,
                  payload={"path": "/tmp/.hidden_dropper.sh"}),
        RawEvent(source=EventSource.PROCESS, event_type="exec", host_info=HOST,
                  payload={"path": "/tmp/.hidden_dropper.sh", "pid": 8842, "user": "www-data"}),
        RawEvent(source=EventSource.NETWORK, event_type="connection", host_info=HOST,
                  payload={"remote_ip": "203.0.113.55", "remote_port": 4444, "flagged": True}),
        RawEvent(source=EventSource.FILESYSTEM, event_type="deleted", host_info=HOST,
                  payload={"path": "/var/log/auth.log"}),
        RawEvent(source=EventSource.FILESYSTEM, event_type="modified", host_info=HOST,
                  payload={"path": "/home/analyst/report_draft.txt"}),
    ]

    for raw_event in eventos_simulados:
        criticality, rule = classifier.classify(raw_event)
        record = chain.append(raw_event, criticality, matched_rule=rule)
        store.append(record)
        print(
            f"[seq={record.seq}] {raw_event.source.value:<10} {raw_event.event_type:<10} "
            f"-> {criticality.value:<8} (regla: {rule or '—'})  hash={record.hash[:12]}..."
        )

    all_records = store.get_all()
    verify_chain(all_records)
    print(f"\n✔ Cadena verificada: {len(all_records)} evidencias íntegras y en orden.")
    store.close()


def caso_2_deteccion_manipulacion(db_path: Path) -> None:
    section("CASO 2 — Detección de manipulación de una evidencia")

    store = EvidenceStore(db_path)  # reabrimos el store del caso 1
    records = store.get_all()

    print("Alguien (o algo) modifica directamente el registro seq=3 en memoria")
    print("(simulando una manipulación de la base de datos)...")
    records[3].event.payload["path"] = "/var/log/system.log"  # <- manipulación

    try:
        verify_chain(records)
        print("✘ ERROR: no se detectó la manipulación (esto no debería pasar)")
    except ChainError as e:
        print(f"✔ Manipulación detectada correctamente:\n  {e}")

    store.close()


def caso_3_reinicio_del_agente(db_path: Path) -> None:
    section("CASO 3 — El agente se reinicia y debe reanudar la cadena")

    # "Apagado" del agente: nueva instancia de store, como si el proceso
    # se hubiera matado y reiniciado
    store = EvidenceStore(db_path)
    last_hash, last_seq = store.get_last_hash_and_seq()
    print(f"Última seq conocida antes del reinicio: {last_seq}")
    print(f"Último hash conocido: {last_hash[:16]}...")

    chain = EvidenceChain(last_hash=last_hash, last_seq=last_seq)
    classifier = ClassifierEngine()

    nuevo_evento = RawEvent(
        source=EventSource.FILESYSTEM, event_type="modified", host_info=HOST,
        payload={"path": "/etc/passwd"},
    )
    criticality, rule = classifier.classify(nuevo_evento)
    record = chain.append(nuevo_evento, criticality, matched_rule=rule)
    store.append(record)

    print(f"Nuevo evento añadido tras el reinicio: seq={record.seq}, prev_hash coincide con el último hash previo: "
          f"{record.prev_hash == last_hash}")

    all_records = store.get_all()
    verify_chain(all_records)
    print(f"✔ Cadena completa (antes y después del reinicio) sigue siendo íntegra: {len(all_records)} registros.")
    store.close()


def caso_4_evidencias_pendientes_de_sync(db_path: Path) -> None:
    section("CASO 4 — Consultar evidencias pendientes de sincronizar")

    store = EvidenceStore(db_path)
    pending = store.get_pending()
    print(f"Evidencias pendientes de enviar al servidor central: {len(pending)}")
    for r in pending[:3]:
        print(f"  - seq={r.seq} criticidad={r.criticality.value} sync_status={r.sync_status}")

    if pending:
        store.mark_synced(pending[0].id)
        print(f"\nMarcada como sincronizada la evidencia seq={pending[0].seq}.")
        print(f"Pendientes ahora: {len(store.get_pending())}")

    store.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "evidence_demo.db"
        caso_1_flujo_normal(db_path)
        caso_2_deteccion_manipulacion(db_path)
        caso_3_reinicio_del_agente(db_path)
        caso_4_evidencias_pendientes_de_sync(db_path)
        print("\n" + "=" * 70)
        print("Fin de la demo.")
        print("=" * 70)
