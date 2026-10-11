"""
Wrapper de servicio de Windows (pywin32). Envuelve al Orchestrator para
que Windows lo gestione como un servicio del sistema (arranque
automático, reinicio ante fallos, etc.), igual que systemd en Linux.

Instalación (con permisos de administrador):
    python windows_service.py install
    python windows_service.py start
    # para desinstalar:
    python windows_service.py remove

Requiere: pip install pywin32
Requiere una variable de entorno EVIDENCE_AGENT_CONFIG apuntando al YAML
de configuración (los servicios de Windows no reciben argv fácilmente).
"""

from __future__ import annotations

import logging
import os
import sys

try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil
except ImportError:  # pragma: no cover - solo instalable/ejecutable en Windows
    win32serviceutil = None

from agent.config import AgentConfig
from agent.orchestrator import Orchestrator


if win32serviceutil is not None:

    class EvidenceAgentService(win32serviceutil.ServiceFramework):
        _svc_name_ = "EvidenceAcquisitionAgent"
        _svc_display_name_ = "Módulo 3 - Agente de Adquisición de Evidencias"
        _svc_description_ = (
            "Monitoriza el sistema, preserva evidencias con integridad "
            "verificable y las sincroniza con el servidor central."
        )

        def __init__(self, args):
            super().__init__(args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.orchestrator: Orchestrator | None = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            if self.orchestrator:
                self.orchestrator.stop()
            win32event.SetEvent(self.stop_event)

        def SvcDoRun(self):
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )
            config_path = os.environ.get("EVIDENCE_AGENT_CONFIG")
            if not config_path:
                servicemanager.LogErrorMsg(
                    "EVIDENCE_AGENT_CONFIG no está definida; no se puede arrancar el agente."
                )
                return

            config = AgentConfig.from_yaml(config_path)
            self.orchestrator = Orchestrator(config)
            self.orchestrator.start()

            servicemanager.LogInfoMsg(f"Agente arrancado (agent_id={config.agent_id}).")
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)


def main() -> None:
    if win32serviceutil is None:
        print("pywin32 no está instalado. Instálalo con: pip install pywin32", file=sys.stderr)
        sys.exit(1)
    win32serviceutil.HandleCommandLine(EvidenceAgentService)


if __name__ == "__main__":
    main()
