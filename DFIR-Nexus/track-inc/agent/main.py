"""
Entry point del agente. Esto es lo que invoca el service wrapper
(systemd / Windows Service / launchd) — ver agent/service/.

Uso manual (para pruebas locales, no como servicio):
    python -m agent.main --config config/agent.example.yaml
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

from agent.config import AgentConfig
from agent.orchestrator import Orchestrator


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run(config_path: str) -> None:
    setup_logging()
    logger = logging.getLogger("agent.main")

    config = AgentConfig.from_yaml(config_path)
    orchestrator = Orchestrator(config)

    stop_requested = False

    def handle_signal(signum, frame):
        nonlocal stop_requested
        logger.info("Señal %s recibida, iniciando apagado ordenado...", signal.Signals(signum).name)
        stop_requested = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    orchestrator.start()
    logger.info("Agente en marcha (agent_id=%s). Ctrl+C para detener.", config.agent_id)

    try:
        # time.sleep(1) en un bucle en vez de signal.pause() porque este
        # último no existe en Windows, y el agente debe ser multiplataforma
        while not stop_requested:
            time.sleep(1)
    finally:
        orchestrator.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Agente de adquisición de evidencias (Módulo 3)")
    parser.add_argument("--config", required=True, help="Ruta al fichero de configuración YAML")
    args = parser.parse_args()

    try:
        run(args.config)
    except Exception as e:
        logging.getLogger("agent.main").exception("Fallo fatal del agente: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
