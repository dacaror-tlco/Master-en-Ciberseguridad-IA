"""
gui/results_panel.py — Panel de resultados con pestañas.
Muestra hosts, puertos, servicios, OS/scripts y salida raw de nmap.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPlainTextEdit, QLabel, QHeaderView, QHBoxLayout, QPushButton,
    QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QBrush

from core.parser import NmapParser, NmapHost


# Colores de estado de puerto
PORT_COLORS = {
    "open":     ("#a6e3a1", "#1e3a2a"),   # text, bg
    "closed":   ("#f38ba8", "#3a1e1e"),
    "filtered": ("#fab387", "#3a2a1e"),
    "open|filtered": ("#f9e2af", "#3a371e"),
}

OS_COLORS = {
    "Linux":   "#89b4fa",
    "Windows": "#cba6f7",
    "FreeBSD": "#a6e3a1",
    "Android": "#a6e3a1",
    "macOS":   "#f5c2e7",
}


class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Barra superior con resumen
        top = QHBoxLayout()
        self.summary_label = QLabel("Sin resultados")
        self.summary_label.setStyleSheet("color: #6c7086; padding: 2px 4px;")
        top.addWidget(self.summary_label)
        top.addStretch()

        self.btn_export_json = QPushButton("Exportar JSON")
        self.btn_export_json.setEnabled(False)
        self.btn_export_json.clicked.connect(self._export_json)
        top.addWidget(self.btn_export_json)
        layout.addLayout(top)

        # Pestañas
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, stretch=1)

        self._tab_hosts    = self._make_hosts_tab()
        self._tab_ports    = self._make_ports_tab()
        self._tab_services = self._make_services_tab()
        self._tab_os       = self._make_os_tab()
        self._tab_scripts  = self._make_scripts_tab()
        self._tab_raw      = self._make_raw_tab()

        self.tabs.addTab(self._tab_hosts,    "🖥  Hosts")
        self.tabs.addTab(self._tab_ports,    "🔌  Puertos")
        self.tabs.addTab(self._tab_services, "⚙  Servicios")
        self.tabs.addTab(self._tab_os,       "🛡  OS / CPE")
        self.tabs.addTab(self._tab_scripts,  "📜  Scripts")
        self.tabs.addTab(self._tab_raw,      "📋  Consola")

        self._hosts_data: list[NmapHost] = []

    # ── Tablas ────────────────────────────────────────────────────────────────

    def _make_table(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        t.horizontalHeader().setStretchLastSection(True)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        return t

    def _make_hosts_tab(self) -> QTableWidget:
        return self._make_table(["IP", "Hostname", "Estado", "SO detectado", "Puertos abiertos"])

    def _make_ports_tab(self) -> QTableWidget:
        return self._make_table(["IP", "Puerto", "Protocolo", "Estado", "Servicio", "Versión"])

    def _make_services_tab(self) -> QTableWidget:
        return self._make_table(["Servicio", "Puerto", "IP", "Versión", "Banner / Extra info"])

    def _make_os_tab(self) -> QTableWidget:
        return self._make_table(["IP", "OS (mejor coincidencia)", "Precisión %", "CPE"])

    def _make_scripts_tab(self) -> QTableWidget:
        t = self._make_table(["IP", "Puerto", "Script", "Resultado"])
        t.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        return t

    def _make_raw_tab(self) -> QPlainTextEdit:
        txt = QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont("JetBrains Mono, Fira Code, Courier New, monospace", 11))
        txt.setMaximumBlockCount(20000)
        return txt

    # ── API pública ───────────────────────────────────────────────────────────

    def clear(self):
        for tab in [self._tab_hosts, self._tab_ports, self._tab_services,
                    self._tab_os, self._tab_scripts]:
            tab.setRowCount(0)
        self._tab_raw.clear()
        self.summary_label.setText("Escaneando…")
        self.summary_label.setStyleSheet("color: #f9e2af; padding: 2px 4px;")
        self.btn_export_json.setEnabled(False)
        self._hosts_data = []

    def append_raw_line(self, line: str):
        """Añade una línea a la consola raw en tiempo real."""
        self._tab_raw.appendPlainText(line)
        # Auto-scroll
        sb = self._tab_raw.verticalScrollBar()
        sb.setValue(sb.maximum())

    def load_xml(self, xml_content: str):
        """Parsea el XML de nmap y rellena todas las pestañas."""
        parser = NmapParser()
        hosts = parser.parse(xml_content)
        self._hosts_data = hosts
        self._populate_hosts(hosts)
        self._populate_ports(hosts)
        self._populate_services(hosts)
        self._populate_os(hosts)
        self._populate_scripts(hosts)

        total_open = sum(
            sum(1 for p in h.ports if p["state"] == "open")
            for h in hosts
        )
        self.summary_label.setText(
            f"✓  {len(hosts)} host(s) —  {total_open} puertos abiertos"
        )
        self.summary_label.setStyleSheet("color: #a6e3a1; padding: 2px 4px;")
        self.btn_export_json.setEnabled(bool(hosts))

    # ── Relleno de pestañas ───────────────────────────────────────────────────

    def _populate_hosts(self, hosts: list):
        t = self._tab_hosts
        t.setRowCount(len(hosts))
        for row, h in enumerate(hosts):
            open_ports = sum(1 for p in h.ports if p["state"] == "open")
            state_color = "#a6e3a1" if h.state == "up" else "#f38ba8"
            items = [
                h.ip,
                ", ".join(h.hostnames) if h.hostnames else "—",
                h.state,
                h.os_name or "Desconocido",
                str(open_ports),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                if col == 2:
                    item.setForeground(QBrush(QColor(state_color)))
                t.setItem(row, col, item)
        t.resizeRowsToContents()

    def _populate_ports(self, hosts: list):
        t = self._tab_ports
        all_ports = [(h.ip, p) for h in hosts for p in h.ports]
        t.setRowCount(len(all_ports))
        for row, (ip, p) in enumerate(all_ports):
            state = p.get("state", "")
            fg, bg = PORT_COLORS.get(state, ("#cdd6f4", "#1e1e2e"))
            items = [
                ip,
                str(p.get("portid", "")),
                p.get("protocol", ""),
                state,
                p.get("service", ""),
                p.get("version", ""),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                if col == 3:
                    item.setForeground(QBrush(QColor(fg)))
                    item.setBackground(QBrush(QColor(bg)))
                t.setItem(row, col, item)
        t.resizeRowsToContents()

    def _populate_services(self, hosts: list):
        t = self._tab_services
        rows = []
        for h in hosts:
            for p in h.ports:
                svc = p.get("service", "")
                if svc:
                    rows.append((
                        svc,
                        f"{p.get('portid','')}/{p.get('protocol','')}",
                        h.ip,
                        p.get("version", ""),
                        p.get("extrainfo", ""),
                    ))
        t.setRowCount(len(rows))
        for row, data in enumerate(rows):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                t.setItem(row, col, item)
        t.resizeRowsToContents()

    def _populate_os(self, hosts: list):
        t = self._tab_os
        rows = []
        for h in hosts:
            if h.os_matches:
                for m in h.os_matches[:2]:  # top 2 coincidencias
                    rows.append((h.ip, m.get("name",""), m.get("accuracy",""), m.get("cpe","")))
            elif h.os_name:
                rows.append((h.ip, h.os_name, "—", ""))
        t.setRowCount(len(rows))
        for row, (ip, name, acc, cpe) in enumerate(rows):
            for col, text in enumerate([ip, name, str(acc), cpe]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                if col == 1:
                    color = next(
                        (c for k, c in OS_COLORS.items() if k in name), "#cdd6f4"
                    )
                    item.setForeground(QBrush(QColor(color)))
                t.setItem(row, col, item)
        t.resizeRowsToContents()

    def _populate_scripts(self, hosts: list):
        t = self._tab_scripts
        rows = []
        for h in hosts:
            for p in h.ports:
                for s in p.get("scripts", []):
                    rows.append((h.ip, f"{p.get('portid','')}/{p.get('protocol','')}", s["id"], s["output"]))
            for s in h.host_scripts:
                rows.append((h.ip, "host", s["id"], s["output"]))
        t.setRowCount(len(rows))
        for row, (ip, port, sid, output) in enumerate(rows):
            for col, text in enumerate([ip, port, sid, output]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter |
                    (Qt.AlignmentFlag.AlignLeft if col == 3 else Qt.AlignmentFlag.AlignLeft)
                )
                if col == 2:
                    item.setForeground(QBrush(QColor("#cba6f7")))
                t.setItem(row, col, item)
        t.resizeRowsToContents()

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _export_json(self):
        import json
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como JSON", "scan_result.json", "JSON (*.json)"
        )
        if not path:
            return
        data = [
            {
                "ip": h.ip,
                "hostnames": h.hostnames,
                "state": h.state,
                "os": h.os_name,
                "ports": h.ports,
                "scripts": h.host_scripts,
            }
            for h in self._hosts_data
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
