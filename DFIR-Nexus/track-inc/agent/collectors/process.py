"""
Collector de procesos. Usa `psutil` (multiplataforma: Linux/Windows/macOS)
en modo polling: cada `poll_interval` segundos compara el conjunto de PIDs
vivos con el de la vuelta anterior.

  - PIDs nuevos  -> evento "exec"
  - PIDs desaparecidos -> evento "terminated"

Nota: el polling puede no capturar procesos de vida muy corta (creados y
terminados entre dos ciclos). Para eso, en fase 2, se puede sustituir o
complementar este collector con hooks nativos (ETW en Windows, eBPF en
Linux vía `bcc`/`libbpf`), pero mantiene el mismo contrato de salida
(RawEvent), así que el resto del agente no se entera del cambio.
"""

from __future__ import annotations

import platform
import socket
import threading
import time

import psutil

from agent.evidence.models import EventSource, HostInfo, RawEvent

from .base import Collector, EventCallback


def _current_host_info(agent_id: str) -> HostInfo:
    return HostInfo(
        agent_id=agent_id,
        hostname=socket.gethostname(),
        os=platform.system().lower(),
    )


def _snapshot_processes() -> dict[int, dict]:
    """Devuelve {pid: info} de todos los procesos vivos ahora mismo.
    Procesos a los que no tenemos acceso (permisos) se omiten sin
    interrumpir el resto del snapshot."""
    snapshot: dict[int, dict] = {}
    for proc in psutil.process_iter(attrs=["pid", "ppid", "name", "exe", "username", "cmdline"]):
        try:
            info = proc.info
            snapshot[info["pid"]] = {
                "pid": info["pid"],
                "ppid": info.get("ppid"),
                "name": info.get("name"),
                "path": info.get("exe") or info.get("name"),
                "user": info.get("username"),
                "cmdline": info.get("cmdline"),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return snapshot


class ProcessCollector(Collector):
    name = "process"

    def __init__(self, on_event: EventCallback, agent_id: str, poll_interval: float = 1.0):
        super().__init__(on_event)
        self.poll_interval = poll_interval
        self.host_info = _current_host_info(agent_id)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_snapshot: dict[int, dict] = {}

    def start(self) -> None:
        self._last_snapshot = _snapshot_processes()  # baseline: no generamos
        # eventos "exec" retroactivos para todo lo que ya estaba corriendo
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.poll_interval + 2)
        self._running = False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)
            current = _snapshot_processes()
            self._diff_and_emit(self._last_snapshot, current)
            self._last_snapshot = current

    def _diff_and_emit(self, before: dict[int, dict], after: dict[int, dict]) -> None:
        new_pids = after.keys() - before.keys()
        gone_pids = before.keys() - after.keys()

        for pid in new_pids:
            self.emit(RawEvent(
                source=EventSource.PROCESS,
                event_type="exec",
                host_info=self.host_info,
                payload=after[pid],
            ))

        for pid in gone_pids:
            self.emit(RawEvent(
                source=EventSource.PROCESS,
                event_type="terminated",
                host_info=self.host_info,
                payload=before[pid],
            ))
