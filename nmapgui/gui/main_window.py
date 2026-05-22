"""
gui/main_window.py — Ventana principal de NmapGUI
Ensambla el panel de configuración, la barra de comando y el panel de resultados.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from gui.config_panel import ConfigPanel
from gui.command_bar import CommandBar
from gui.results_panel import ResultsPanel
from core.runner import NmapRunner


class ScanThread(QThread):
    """Hilo para ejecutar nmap sin bloquear la GUI."""
    line_received = pyqtSignal(str)
    finished = pyqtSignal(int, str)   # returncode, xml_output

    def __init__(self, command: list[str]):
        super().__init__()
        self.command = command
        self._runner = NmapRunner()

    def run(self):
        self._runner.run(
            self.command,
            on_line=self.line_received.emit,
            on_done=self.finished.emit,
        )

    def stop(self):
        self._runner.stop()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NmapGUI  —  Escáner de red")
        self.resize(1280, 820)
        self._scan_thread: ScanThread | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Barra de comando (arriba)
        self.cmd_bar = CommandBar()
        self.cmd_bar.scan_requested.connect(self._on_scan)
        self.cmd_bar.stop_requested.connect(self._on_stop)
        root.addWidget(self.cmd_bar)

        # Splitter horizontal: config | resultados
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.config_panel = ConfigPanel()
        self.config_panel.command_changed.connect(self.cmd_bar.set_command)
        splitter.addWidget(self.config_panel)

        self.results_panel = ResultsPanel()
        splitter.addWidget(self.results_panel)

        splitter.setSizes([370, 900])
        root.addWidget(splitter, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status_label = QLabel("Listo")
        self.status_bar.addWidget(self._status_label)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_scan(self, command: list[str]):
        if self._scan_thread and self._scan_thread.isRunning():
            return

        self.results_panel.clear()
        self._status_label.setText(f"Ejecutando: {' '.join(command)}")
        self.cmd_bar.set_running(True)

        self._scan_thread = ScanThread(command)
        self._scan_thread.line_received.connect(self.results_panel.append_raw_line)
        self._scan_thread.finished.connect(self._on_scan_done)
        self._scan_thread.start()

    def _on_stop(self):
        if self._scan_thread:
            self._scan_thread.stop()

    def _on_scan_done(self, returncode: int, xml_output: str):
        self.cmd_bar.set_running(False)
        if returncode == 0:
            self._status_label.setText("Escaneo completado ✓")
            self.results_panel.load_xml(xml_output)
        elif returncode == -1:
            self._status_label.setText("Escaneo cancelado")
        else:
            self._status_label.setText(f"Nmap terminó con código {returncode}")
