"""
gui/command_bar.py — Barra superior con preview del comando y controles de escaneo.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit,
    QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class CommandBar(QWidget):
    """
    Muestra el comando nmap generado en tiempo real,
    permite editarlo manualmente y lanzar/detener el escaneo.
    """

    scan_requested = pyqtSignal(list)    # emite la lista de args al lanzar
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._current_command: list[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("$ ")
        label.setStyleSheet("color: #a6e3a1; font-family: monospace; font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        self.cmd_edit = QLineEdit()
        self.cmd_edit.setPlaceholderText("El comando nmap aparecerá aquí — también puedes editarlo manualmente")
        self.cmd_edit.setFont(QFont("JetBrains Mono, Fira Code, Courier New, monospace", 12))
        self.cmd_edit.setStyleSheet(
            "background-color: #181825; border: 1px solid #45475a; border-radius: 4px;"
            "color: #a6e3a1; padding: 6px 10px; font-family: monospace;"
        )
        layout.addWidget(self.cmd_edit, stretch=1)

        self.btn_copy = QPushButton("Copiar")
        self.btn_copy.setFixedWidth(72)
        self.btn_copy.setStyleSheet(
            "background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;"
            "border-radius: 4px; padding: 6px 10px;"
        )
        self.btn_copy.clicked.connect(self._copy_command)
        layout.addWidget(self.btn_copy)

        self.btn_scan = QPushButton("▶  Escanear")
        self.btn_scan.setFixedWidth(120)
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        layout.addWidget(self.btn_scan)

        self.btn_stop = QPushButton("■  Detener")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setFixedWidth(110)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        layout.addWidget(self.btn_stop)

    # ── Slots públicos ────────────────────────────────────────────────────────

    def set_command(self, args: list[str]):
        """Actualiza el campo de texto con el nuevo comando."""
        self._current_command = args
        self.cmd_edit.setText(" ".join(args))

    def set_running(self, running: bool):
        """Cambia el estado visual según si hay un escaneo activo."""
        self.btn_scan.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.cmd_edit.setReadOnly(running)
        if running:
            self.btn_scan.setText("⏳ Escaneando…")
        else:
            self.btn_scan.setText("▶  Escanear")

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _on_scan_clicked(self):
        raw = self.cmd_edit.text().strip()
        if not raw:
            return
        # Permite que el usuario edite el comando libremente
        args = raw.split()
        self.scan_requested.emit(args)

    def _copy_command(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.cmd_edit.text())
        original = self.btn_copy.text()
        self.btn_copy.setText("✓ Copiado")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(original))
