"""
Persistencia local de EvidenceRecord en SQLite, en modo append-only:
no hay UPDATE ni DELETE sobre el contenido de la evidencia (solo se
permite actualizar `sync_status`, que es metadato de transporte, no
evidencia en sí).
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .chain import GENESIS_HASH
from .models import Criticality, EventSource, EvidenceRecord, HostInfo, RawEvent

SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_records (
    seq INTEGER PRIMARY KEY,
    record_id TEXT NOT NULL UNIQUE,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    criticality TEXT NOT NULL,
    matched_rule TEXT,
    sync_status TEXT NOT NULL DEFAULT 'pending',
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class EvidenceStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        # check_same_thread=False: los collectors (filesystem, procesos, red)
        # corren en sus propios hilos (p. ej. watchdog) y todos escriben al
        # mismo store. Protegemos los accesos con un Lock explícito en vez
        # de depender del modo por defecto de sqlite3.
        # timeout: si otro proceso/hilo tiene la escritura bloqueada (ver
        # transaccion_exclusiva), se espera en vez de fallar al instante.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        # RLock: append() se llama también DENTRO de transaccion_exclusiva(),
        # que ya tiene el lock tomado.
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute(SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- escritura -----------------------------------------------------

    @contextmanager
    def transaccion_exclusiva(self) -> Iterator[None]:
        """Reserva la escritura del fichero hasta confirmar o deshacer.

        `BEGIN IMMEDIATE` bloquea a cualquier otro escritor, también de
        otro proceso, desde antes de leer el último eslabón. Sin esto, dos
        guardados simultáneos leían el mismo `seq` y el segundo chocaba al
        insertar. Dentro del bloque, `append(..., commit=False)`.
        """
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self._conn.rollback()
                raise
            self._conn.commit()

    def append(self, record: EvidenceRecord, commit: bool = True) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO evidence_records
                    (seq, record_id, prev_hash, hash, criticality, matched_rule, sync_status, event_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.seq,
                    record.id,
                    record.prev_hash,
                    record.hash,
                    record.criticality.value,
                    record.matched_rule,
                    record.sync_status,
                    record.event.model_dump_json(),
                ),
            )
            if commit:
                self._conn.commit()

    def mark_synced(self, record_id: str, status: str = "acked") -> None:
        """Único UPDATE permitido: el estado de sincronización, que no
        forma parte del material hasheado."""
        with self._lock:
            self._conn.execute(
                "UPDATE evidence_records SET sync_status = ? WHERE record_id = ?",
                (status, record_id),
            )
            self._conn.commit()

    # -- lectura ---------------------------------------------------------

    def get_last_hash_and_seq(self) -> tuple[str, int]:
        row = self._conn.execute(
            "SELECT hash, seq FROM evidence_records ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return GENESIS_HASH, -1
        return row[0], row[1]

    def get_pending(self, limit: int = 100) -> list[EvidenceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM evidence_records WHERE sync_status = 'pending' ORDER BY seq ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get_all(self) -> list[EvidenceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM evidence_records ORDER BY seq ASC"
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: tuple) -> EvidenceRecord:
        # columnas: seq, record_id, prev_hash, hash, criticality, matched_rule, sync_status, event_json, created_at
        seq, record_id, prev_hash, hash_, criticality, matched_rule, sync_status, event_json, _created_at = row
        event = RawEvent.model_validate_json(event_json)
        return EvidenceRecord(
            id=record_id,
            event=event,
            criticality=Criticality(criticality),
            matched_rule=matched_rule,
            seq=seq,
            prev_hash=prev_hash,
            hash=hash_,
            sync_status=sync_status,
        )
