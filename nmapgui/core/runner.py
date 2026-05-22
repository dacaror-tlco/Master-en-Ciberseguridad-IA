"""
core/runner.py — Motor de ejecución de nmap.
Lanza el proceso, emite líneas en tiempo real y devuelve el XML al terminar.
"""

import subprocess
import os
import signal
from typing import Callable


class NmapRunner:
    """
    Ejecuta nmap como subproceso.
    - on_line(str):       llamado por cada línea de stdout en tiempo real.
    - on_done(int, str):  llamado al terminar con (returncode, xml_content).
    """

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._stopped = False

    def run(
        self,
        command: list[str],
        on_line: Callable[[str], None],
        on_done: Callable[[int, str], None],
    ):
        self._stopped = False

        # Asegurar que el directorio exports existe
        os.makedirs("exports", exist_ok=True)

        # Extraer ruta del XML de los args (-oX <path>)
        xml_path = self._extract_xml_path(command)

        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,          # line-buffered
                encoding="utf-8",
                errors="replace",
            )

            # Streaming línea a línea
            for line in self._process.stdout:
                line = line.rstrip("\n")
                on_line(line)
                if self._stopped:
                    break

            self._process.wait()
            returncode = self._process.returncode

            if self._stopped:
                on_done(-1, "")
                return

            # Leer el XML generado por nmap
            xml_content = ""
            if xml_path and os.path.exists(xml_path):
                with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
                    xml_content = f.read()
            else:
                on_line("[NmapGUI] Aviso: no se encontró el fichero XML de salida.")
                on_line(f"[NmapGUI] Ruta esperada: {xml_path}")

            on_done(returncode, xml_content)

        except FileNotFoundError:
            on_line("[NmapGUI] ERROR: nmap no encontrado. Instálalo con: sudo apt install nmap")
            on_done(127, "")
        except PermissionError:
            on_line("[NmapGUI] ERROR: Permiso denegado. Algunos tipos de scan requieren sudo.")
            on_done(1, "")
        except Exception as e:
            on_line(f"[NmapGUI] ERROR inesperado: {e}")
            on_done(1, "")

    def stop(self):
        """Detiene el proceso nmap en curso."""
        self._stopped = True
        if self._process and self._process.poll() is None:
            try:
                # Intentar terminar el grupo de procesos (incluye sudo + nmap)
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                try:
                    self._process.terminate()
                except Exception:
                    pass

    @staticmethod
    def _extract_xml_path(command: list[str]) -> str | None:
        """Extrae la ruta del XML del listado de argumentos."""
        for i, arg in enumerate(command):
            if arg == "-oX" and i + 1 < len(command):
                return command[i + 1]
        return None
