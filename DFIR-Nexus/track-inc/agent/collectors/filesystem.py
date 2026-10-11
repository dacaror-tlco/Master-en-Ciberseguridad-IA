"""
Collector de filesystem. Usa `watchdog`, que abstrae:
  - inotify en Linux
  - ReadDirectoryChangesW en Windows
  - FSEvents en macOS

Traduce los eventos nativos de watchdog al esquema normalizado RawEvent.
"""

from __future__ import annotations

import platform
import socket

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from agent.evidence.models import EventSource, HostInfo, RawEvent

from .base import Collector, EventCallback

_WATCHDOG_TO_INTERNAL = {
    "created": "created",
    "deleted": "deleted",
    "modified": "modified",
    "moved": "moved",
}
# watchdog también emite "opened"/"closed" (y variantes) en algunas
# plataformas; son ruido para propósitos forenses y no aportan valor de
# evidencia por sí solos, así que se descartan explícitamente aquí.
_IGNORED_WATCHDOG_TYPES = {"opened", "closed", "closed_no_write"}


def _current_host_info(agent_id: str) -> HostInfo:
    return HostInfo(
        agent_id=agent_id,
        hostname=socket.gethostname(),
        os=platform.system().lower(),  # "linux" | "windows" | "darwin"
    )


class _Handler(FileSystemEventHandler):
    def __init__(self, collector: "FilesystemCollector"):
        self._collector = collector

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return  # de momento solo nos interesan ficheros, no directorios
        if event.event_type in _IGNORED_WATCHDOG_TYPES:
            return

        event_type = _WATCHDOG_TO_INTERNAL.get(event.event_type, event.event_type)
        payload = {
            "path": event.src_path,
            "watchdog_event_type": event.event_type,
        }
        if event.event_type == "moved":
            payload["dest_path"] = getattr(event, "dest_path", None)

        raw_event = RawEvent(
            source=EventSource.FILESYSTEM,
            event_type=event_type,
            host_info=self._collector.host_info,
            payload=payload,
        )
        self._collector.emit(raw_event)


class FilesystemCollector(Collector):
    name = "filesystem"

    def __init__(self, on_event: EventCallback, watch_paths: list[str], agent_id: str, recursive: bool = True):
        super().__init__(on_event)
        self.watch_paths = watch_paths
        self.recursive = recursive
        self.host_info = _current_host_info(agent_id)
        self._observer = Observer()

    def start(self) -> None:
        handler = _Handler(self)
        for path in self.watch_paths:
            self._observer.schedule(handler, path, recursive=self.recursive)
        self._observer.start()
        self._running = True

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)
        self._running = False
