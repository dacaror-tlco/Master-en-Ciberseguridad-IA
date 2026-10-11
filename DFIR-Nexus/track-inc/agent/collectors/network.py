"""
Collector de red. Igual que el de procesos, usa `psutil` en modo polling
sobre `psutil.net_connections()`, comparando el conjunto de conexiones
activas entre ciclos.

Marca `flagged=True` cuando la IP remota coincide con una lista negra
simple (para que el clasificador la reconozca vía la regla
`conexion_saliente_sospechosa`). La lista negra real debería venir del
Módulo 2 (OSINT/fraude) — aquí se deja como parámetro inyectable para no
acoplar este collector a esa integración todavía.
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


def _connection_key(conn) -> tuple:
    laddr = tuple(conn.laddr) if conn.laddr else ()
    raddr = tuple(conn.raddr) if conn.raddr else ()
    return (conn.pid, laddr, raddr, conn.status)


def _snapshot_connections() -> dict[tuple, dict]:
    snapshot: dict[tuple, dict] = {}
    try:
        connections = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        # en algunos SOs hace falta ser root/admin para ver todas las
        # conexiones; se puede acotar con permisos elevados para el
        # servicio, pero no debe tumbar el collector si no los tiene
        connections = []

    for conn in connections:
        key = _connection_key(conn)
        snapshot[key] = {
            "pid": conn.pid,
            "local_ip": conn.laddr.ip if conn.laddr else None,
            "local_port": conn.laddr.port if conn.laddr else None,
            "remote_ip": conn.raddr.ip if conn.raddr else None,
            "remote_port": conn.raddr.port if conn.raddr else None,
            "status": conn.status,
        }
    return snapshot


class NetworkCollector(Collector):
    name = "network"

    def __init__(
        self,
        on_event: EventCallback,
        agent_id: str,
        poll_interval: float = 2.0,
        ip_blacklist: set[str] | None = None,
    ):
        super().__init__(on_event)
        self.poll_interval = poll_interval
        self.host_info = _current_host_info(agent_id)
        self.ip_blacklist = ip_blacklist or set()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_snapshot: dict[tuple, dict] = {}

    def start(self) -> None:
        self._last_snapshot = _snapshot_connections()
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
            current = _snapshot_connections()
            self._diff_and_emit(self._last_snapshot, current)
            self._last_snapshot = current

    def _diff_and_emit(self, before: dict[tuple, dict], after: dict[tuple, dict]) -> None:
        new_keys = after.keys() - before.keys()
        for key in new_keys:
            payload = dict(after[key])
            payload["flagged"] = payload.get("remote_ip") in self.ip_blacklist
            self.emit(RawEvent(
                source=EventSource.NETWORK,
                event_type="connection",
                host_info=self.host_info,
                payload=payload,
            ))
