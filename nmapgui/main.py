#!/usr/bin/env python3
"""
NmapGUI - Interfaz gráfica para nmap
Máster en Ciberseguridad e IA
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NmapGUI")
    app.setApplicationVersion("1.0")
    app.setStyle("Fusion")

    # Hoja de estilos global (dark theme)
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            border: 1px solid #45475a;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 8px;
            font-weight: bold;
            color: #89b4fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
        }
        QLabel { color: #cdd6f4; }
        QLineEdit, QSpinBox, QComboBox {
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 4px;
            padding: 4px 8px;
            color: #cdd6f4;
        }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
            border: 1px solid #89b4fa;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #313244;
            border: 1px solid #45475a;
            selection-background-color: #45475a;
        }
        QCheckBox { color: #cdd6f4; spacing: 6px; }
        QCheckBox::indicator {
            width: 15px; height: 15px;
            border: 1px solid #45475a;
            border-radius: 3px;
            background-color: #313244;
        }
        QCheckBox::indicator:checked {
            background-color: #89b4fa;
            border-color: #89b4fa;
        }
        QPushButton {
            background-color: #89b4fa;
            color: #1e1e2e;
            border: none;
            border-radius: 5px;
            padding: 7px 18px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #b4befe; }
        QPushButton:pressed { background-color: #74c7ec; }
        QPushButton:disabled {
            background-color: #45475a;
            color: #6c7086;
        }
        QPushButton#btn_stop {
            background-color: #f38ba8;
            color: #1e1e2e;
        }
        QPushButton#btn_stop:hover { background-color: #eba0ac; }
        QTabWidget::pane {
            border: 1px solid #45475a;
            border-radius: 0 6px 6px 6px;
        }
        QTabBar::tab {
            background-color: #313244;
            color: #6c7086;
            padding: 7px 16px;
            border: 1px solid #45475a;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #1e1e2e;
            color: #cdd6f4;
            border-bottom: 2px solid #89b4fa;
        }
        QTabBar::tab:hover:!selected { background-color: #45475a; }
        QTextEdit, QPlainTextEdit {
            background-color: #181825;
            border: 1px solid #45475a;
            border-radius: 4px;
            color: #a6e3a1;
            font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
            font-size: 12px;
        }
        QTableWidget {
            background-color: #181825;
            border: 1px solid #45475a;
            border-radius: 4px;
            gridline-color: #313244;
            alternate-background-color: #1e1e2e;
        }
        QTableWidget::item { padding: 4px 8px; color: #cdd6f4; }
        QTableWidget::item:selected { background-color: #45475a; }
        QHeaderView::section {
            background-color: #313244;
            color: #89b4fa;
            padding: 6px 8px;
            border: none;
            border-right: 1px solid #45475a;
            border-bottom: 1px solid #45475a;
            font-weight: bold;
        }
        QScrollBar:vertical {
            background: #1e1e2e; width: 8px; border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #45475a; border-radius: 4px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #6c7086; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QProgressBar {
            border: 1px solid #45475a;
            border-radius: 4px;
            text-align: center;
            background-color: #313244;
            color: #cdd6f4;
        }
        QProgressBar::chunk {
            background-color: #89b4fa;
            border-radius: 3px;
        }
        QSplitter::handle { background-color: #45475a; }
        QSplitter::handle:horizontal { width: 2px; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
