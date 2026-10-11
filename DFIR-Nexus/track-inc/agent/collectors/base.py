"""
Interfaz base de un Collector. Cada collector real (filesystem, procesos,
red) la implementa. El orquestador solo conoce esta interfaz, nunca los
detalles internos de cada collector -> así se pueden activar/desactivar
o añadir nuevos sin tocar el resto del agente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from agent.evidence.models import RawEvent

# callback que el orquestador registra para recibir cada evento crudo
EventCallback = Callable[[RawEvent], None]


class Collector(ABC):
    name: str = "base"

    def __init__(self, on_event: EventCallback):
        self._on_event = on_event
        self._running = False

    @abstractmethod
    def start(self) -> None:
        """Arranca la monitorización (no bloqueante)."""

    @abstractmethod
    def stop(self) -> None:
        """Detiene la monitorización de forma ordenada."""

    def emit(self, event: RawEvent) -> None:
        """Los subtipos llaman a esto cuando detectan un evento."""
        self._on_event(event)

    @property
    def running(self) -> bool:
        return self._running
