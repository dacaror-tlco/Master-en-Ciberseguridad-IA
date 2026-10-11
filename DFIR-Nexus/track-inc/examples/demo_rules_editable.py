"""
Demo del caso de uso principal de rules.yaml: un analista (o el equipo
de OSINT del Módulo 2) ajusta la criticidad de una regla, o añade una
regla nueva, SIN tocar ni una línea de Python.

Ejecutar con:
    python -m examples.demo_rules_editable
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent.classifier.engine import ClassifierEngine
from agent.evidence.models import EventSource, HostInfo, RawEvent

HOST = HostInfo(agent_id="agent-demo", hostname="workstation", os="linux")

BASE_RULES = """
rules:
  - name: acceso_a_wallet_crypto
    criticality: MEDIUM
    conditions:
      source: filesystem
      event_type: modified
      payload.path: ["wallet.dat", ".electrum"]
default_criticality: LOW
"""


def classify_and_print(engine: ClassifierEngine, label: str) -> None:
    event = RawEvent(
        source=EventSource.FILESYSTEM, event_type="modified", host_info=HOST,
        payload={"path": "/home/user/.electrum/wallets/wallet.dat"},
    )
    criticality, rule = engine.classify(event)
    print(f"{label}: acceso a wallet.dat -> {criticality.value} (regla: {rule})")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = Path(tmp) / "rules.yaml"
        rules_path.write_text(BASE_RULES)

        print("=== Paso 1: reglas iniciales ===")
        engine_v1 = ClassifierEngine.from_yaml(rules_path)
        classify_and_print(engine_v1, "Antes  ")

        print("\n=== Paso 2: el equipo de fraude detecta una campaña activa ===")
        print("contra carteras cripto y sube la criticidad, editando SOLO el YAML...\n")

        updated_rules = BASE_RULES.replace("criticality: MEDIUM", "criticality: CRITICAL")
        rules_path.write_text(updated_rules)

        # En el agente real, esto se dispararía por un watcher sobre el propio
        # fichero de reglas, o por un simple reinicio del proceso de clasificación;
        # aquí lo hacemos explícito para que se vea el efecto:
        engine_v2 = ClassifierEngine.from_yaml(rules_path)
        classify_and_print(engine_v2, "Después")

        print("\n✔ El comportamiento cambió sin tocar ni una línea de código Python.")


if __name__ == "__main__":
    main()
