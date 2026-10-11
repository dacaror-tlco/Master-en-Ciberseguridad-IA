"""
Cadena de hashes (hash chaining) para garantizar integridad y orden
cronológico de las evidencias.

Idea: cada EvidenceRecord contiene el hash del registro anterior. El hash
de un registro se calcula sobre (prev_hash + contenido_canónico). Si
alguien modifica, borra o reordena un registro intermedio, el hash de
todos los registros posteriores deja de coincidir -> se detecta.

    genesis_hash <- record_0.hash <- record_1.hash <- record_2.hash <- ...
"""

from __future__ import annotations

import hashlib
import json
import threading

from .models import Criticality, EvidenceRecord, RawEvent

GENESIS_HASH = "0" * 64  # hash "cero" que abre cualquier cadena nueva


def canonical_json(data: dict) -> str:
    """JSON determinista: claves ordenadas, sin espacios superfluos.
    Imprescindible para que el mismo contenido siempre produzca el mismo
    hash, sin importar en qué máquina o cuándo se serializó."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(prev_hash: str, payload: dict) -> str:
    material = prev_hash + canonical_json(payload)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class ChainError(Exception):
    """Se lanza cuando la cadena de evidencias está rota o manipulada."""


class EvidenceChain:
    """
    Construye la cadena en memoria/proceso. La persistencia real (SQLite)
    vive en store.py; esta clase se centra solo en la lógica de hashing
    y verificación, para que sea fácil de testear de forma aislada.
    """

    def __init__(self, last_hash: str | None = None, last_seq: int = -1):
        # last_hash/last_seq permiten "reanudar" una cadena tras un
        # reinicio del agente (se recuperan del store local o del server).
        self._last_hash = last_hash or GENESIS_HASH
        self._last_seq = last_seq
        # Varios collectors (hilos distintos) pueden llamar a append() a
        # la vez -> sin lock, dos eventos podrían calcular su prev_hash
        # sobre el mismo last_hash y "pisarse" la cadena.
        self._lock = threading.Lock()

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def last_seq(self) -> int:
        return self._last_seq

    def append(
        self,
        event: RawEvent,
        criticality: Criticality,
        matched_rule: str | None = None,
    ) -> EvidenceRecord:
        """Crea el siguiente EvidenceRecord de la cadena, ya enlazado."""
        with self._lock:
            seq = self._last_seq + 1
            record = EvidenceRecord(
                event=event,
                criticality=criticality,
                matched_rule=matched_rule,
                seq=seq,
                prev_hash=self._last_hash,
                hash="",  # se calcula a continuación
            )
            record.hash = compute_hash(record.prev_hash, record.canonical_payload_for_hash())

            self._last_hash = record.hash
            self._last_seq = seq
            return record


def verify_chain(records: list[EvidenceRecord]) -> None:
    """
    Verifica una secuencia de EvidenceRecord de principio a fin.
    Lanza ChainError con un mensaje claro en cuanto encuentra el primer
    eslabón roto. No lanza nada si la cadena es íntegra.

    Se asume que `records` viene ordenado por `seq` ascendente.
    """
    if not records:
        return

    expected_prev = records[0].prev_hash  # aceptamos el punto de partida que traiga
    expected_seq = records[0].seq

    for record in records:
        if record.seq != expected_seq:
            raise ChainError(
                f"Hueco o desorden en la secuencia: esperado seq={expected_seq}, "
                f"encontrado seq={record.seq} (record id={record.id})"
            )
        if record.prev_hash != expected_prev:
            raise ChainError(
                f"prev_hash no coincide en seq={record.seq}: "
                f"esperado {expected_prev}, encontrado {record.prev_hash}"
            )
        recomputed = compute_hash(record.prev_hash, record.canonical_payload_for_hash())
        if recomputed != record.hash:
            raise ChainError(
                f"Hash inválido en seq={record.seq} (record id={record.id}): "
                f"el contenido fue modificado tras su creación. "
                f"Esperado {record.hash}, recalculado {recomputed}."
            )

        expected_prev = record.hash
        expected_seq += 1
