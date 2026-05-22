"""
gui/config_panel.py — Panel de configuración de parámetros nmap
Genera el comando nmap en tiempo real conforme el usuario ajusta opciones.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QGroupBox, QLabel, QLineEdit, QCheckBox,
    QComboBox, QSpinBox, QRadioButton, QButtonGroup,
    QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt


class ConfigPanel(QWidget):
    """Panel izquierdo: selección de parámetros → emite command_changed."""

    command_changed = pyqtSignal(list)   # lista de argumentos para nmap

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(340)
        self.setMaximumWidth(420)
        self._build_ui()
        self._connect_all()
        self._rebuild_command()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(self._build_target())
        layout.addWidget(self._build_scan_type())
        layout.addWidget(self._build_ports())
        layout.addWidget(self._build_timing())
        layout.addWidget(self._build_detection())
        layout.addWidget(self._build_output())
        layout.addWidget(self._build_scripts())
        layout.addWidget(self._build_extra())
        layout.addStretch()

    # ── Grupos ────────────────────────────────────────────────────────────────

    def _build_target(self):
        grp = QGroupBox("🎯  Objetivo")
        lay = QVBoxLayout(grp)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("192.168.1.0/24  |  10.0.0.1  |  ejemplo.com")
        lay.addWidget(QLabel("Host / Rango / CIDR:"))
        lay.addWidget(self.target_input)

        self.chk_exclude = QCheckBox("Excluir hosts")
        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("192.168.1.1,192.168.1.254")
        self.exclude_input.setEnabled(False)
        self.chk_exclude.toggled.connect(self.exclude_input.setEnabled)
        lay.addWidget(self.chk_exclude)
        lay.addWidget(self.exclude_input)
        return grp

    def _build_scan_type(self):
        grp = QGroupBox("🔍  Tipo de escaneo")
        lay = QVBoxLayout(grp)
        self._scan_group = QButtonGroup(self)

        scan_types = [
            ("-sS", "SYN Stealth (default)"),
            ("-sT", "TCP Connect"),
            ("-sU", "UDP"),
            ("-sN", "Null scan"),
            ("-sF", "FIN scan"),
            ("-sX", "Xmas scan"),
            ("-sA", "ACK scan"),
            ("-sn", "Ping scan (sin puertos)"),
            ("-Pn", "Sin ping (asumir activo)"),
        ]
        for flag, label in scan_types:
            rb = QRadioButton(label)
            rb.setProperty("flag", flag)
            if flag == "-sS":
                rb.setChecked(True)
            self._scan_group.addButton(rb)
            lay.addWidget(rb)
        return grp

    def _build_ports(self):
        grp = QGroupBox("🔌  Puertos")
        lay = QVBoxLayout(grp)

        self.port_mode = QComboBox()
        self.port_mode.addItems([
            "Top 1000 (default)",
            "Todos los puertos (-p-)",
            "Top 100 (--top-ports 100)",
            "Personalizado",
        ])
        lay.addWidget(self.port_mode)

        self.port_custom = QLineEdit()
        self.port_custom.setPlaceholderText("22,80,443  |  1-1024  |  U:53,T:80")
        self.port_custom.setEnabled(False)
        self.port_mode.currentIndexChanged.connect(
            lambda i: self.port_custom.setEnabled(i == 3)
        )
        lay.addWidget(self.port_custom)

        self.chk_fast = QCheckBox("-F  Modo rápido (100 puertos más comunes)")
        lay.addWidget(self.chk_fast)
        return grp

    def _build_timing(self):
        grp = QGroupBox("⏱  Timing")
        lay = QVBoxLayout(grp)

        timings = [
            ("T0", "Paranoico — IDS evasion"),
            ("T1", "Sigiloso"),
            ("T2", "Educado"),
            ("T3", "Normal (default)"),
            ("T4", "Agresivo"),
            ("T5", "Insano"),
        ]
        self.timing_combo = QComboBox()
        for t, desc in timings:
            self.timing_combo.addItem(f"-{t}  {desc}", t)
        self.timing_combo.setCurrentIndex(3)
        lay.addWidget(self.timing_combo)

        row = QHBoxLayout()
        row.addWidget(QLabel("Max retries:"))
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(3)
        row.addWidget(self.max_retries)
        lay.addLayout(row)
        return grp

    def _build_detection(self):
        grp = QGroupBox("🛡  Detección")
        lay = QVBoxLayout(grp)

        self.chk_os      = QCheckBox("-O   Detección de SO")
        self.chk_version = QCheckBox("-sV  Detección de versión de servicios")
        self.chk_verbose = QCheckBox("-v   Verbose")
        self.chk_reason  = QCheckBox("--reason  Mostrar razón del estado del puerto")
        self.chk_tracert = QCheckBox("--traceroute  Trazar ruta")
        lay.addWidget(self.chk_os)
        lay.addWidget(self.chk_version)

        row = QHBoxLayout()
        row.addWidget(QLabel("Intensidad versión:"))
        self.version_intensity = QSpinBox()
        self.version_intensity.setRange(0, 9)
        self.version_intensity.setValue(5)
        self.version_intensity.setEnabled(False)
        self.chk_version.toggled.connect(self.version_intensity.setEnabled)
        row.addWidget(self.version_intensity)
        lay.addLayout(row)

        lay.addWidget(self.chk_verbose)
        lay.addWidget(self.chk_reason)
        lay.addWidget(self.chk_tracert)
        return grp

    def _build_output(self):
        grp = QGroupBox("💾  Salida / Exportar")
        lay = QVBoxLayout(grp)

        self.chk_save_xml  = QCheckBox("Guardar XML  (-oX)")
        self.chk_save_txt  = QCheckBox("Guardar texto  (-oN)")
        self.chk_save_json = QCheckBox("Guardar grepable  (-oG)")

        self.output_name = QLineEdit("scan_result")
        self.output_name.setPlaceholderText("nombre base del fichero")
        lay.addWidget(QLabel("Nombre base:"))
        lay.addWidget(self.output_name)
        lay.addWidget(self.chk_save_xml)
        lay.addWidget(self.chk_save_txt)
        lay.addWidget(self.chk_save_json)
        return grp

    def _build_scripts(self):
        grp = QGroupBox("📜  Scripts NSE")
        lay = QVBoxLayout(grp)

        self.chk_default_scripts = QCheckBox("-sC  Scripts por defecto")
        lay.addWidget(self.chk_default_scripts)

        script_presets = [
            ("(ninguno)", ""),
            ("vuln — Vulnerabilidades", "vuln"),
            ("auth — Autenticación", "auth"),
            ("discovery — Descubrimiento", "discovery"),
            ("safe — Solo scripts seguros", "safe"),
            ("exploit — Exploits", "exploit"),
            ("brute — Fuerza bruta", "brute"),
            ("malware — Detección malware", "malware"),
            ("http-* — Scripts HTTP", "http-*"),
            ("smb-* — Scripts SMB", "smb-*"),
            ("ssh-* — Scripts SSH", "ssh-*"),
            ("ftp-* — Scripts FTP", "ftp-*"),
        ]
        self.script_combo = QComboBox()
        for label, val in script_presets:
            self.script_combo.addItem(label, val)
        lay.addWidget(QLabel("Script/categoría:"))
        lay.addWidget(self.script_combo)

        self.custom_script = QLineEdit()
        self.custom_script.setPlaceholderText("script personalizado o args extra")
        lay.addWidget(QLabel("Script personalizado:"))
        lay.addWidget(self.custom_script)
        return grp

    def _build_extra(self):
        grp = QGroupBox("⚙  Opciones extra")
        lay = QVBoxLayout(grp)

        self.chk_aggressive = QCheckBox("-A   Modo agresivo (OS+versión+script+traceroute)")
        self.chk_ipv6       = QCheckBox("-6   Escaneo IPv6")
        self.chk_privileged = QCheckBox("Ejecutar con sudo (necesario para SYN)")
        self.chk_privileged.setChecked(True)
        lay.addWidget(self.chk_aggressive)
        lay.addWidget(self.chk_ipv6)
        lay.addWidget(self.chk_privileged)

        self.extra_args = QLineEdit()
        self.extra_args.setPlaceholderText("Argumentos adicionales libres")
        lay.addWidget(QLabel("Args adicionales:"))
        lay.addWidget(self.extra_args)
        return grp

    # ── Señales ───────────────────────────────────────────────────────────────

    def _connect_all(self):
        """Conecta todos los widgets para que cualquier cambio regenere el comando."""
        widgets = [
            self.target_input, self.exclude_input, self.port_custom,
            self.output_name, self.custom_script, self.extra_args,
        ]
        for w in widgets:
            w.textChanged.connect(self._rebuild_command)

        checkboxes = [
            self.chk_exclude, self.chk_fast, self.chk_os, self.chk_version,
            self.chk_verbose, self.chk_reason, self.chk_tracert,
            self.chk_save_xml, self.chk_save_txt, self.chk_save_json,
            self.chk_default_scripts, self.chk_aggressive,
            self.chk_ipv6, self.chk_privileged,
        ]
        for cb in checkboxes:
            cb.toggled.connect(self._rebuild_command)

        combos = [self.port_mode, self.timing_combo, self.script_combo]
        for combo in combos:
            combo.currentIndexChanged.connect(self._rebuild_command)

        self._scan_group.buttonToggled.connect(self._rebuild_command)
        self.max_retries.valueChanged.connect(self._rebuild_command)
        self.version_intensity.valueChanged.connect(self._rebuild_command)

    # ── Construcción del comando ──────────────────────────────────────────────

    def _rebuild_command(self, *_):
        args = []

        if self.chk_privileged.isChecked():
            args.append("sudo")

        args.append("nmap")

        # Tipo de escaneo
        checked_btn = self._scan_group.checkedButton()
        if checked_btn:
            flag = checked_btn.property("flag")
            if flag not in ("-sS",):   # -sS es el default silencioso de nmap
                args.append(flag)
            elif flag == "-sS":
                args.append("-sS")

        # Modo agresivo (sobreescribe otros)
        if self.chk_aggressive.isChecked():
            args.append("-A")
        else:
            if self.chk_os.isChecked():
                args.append("-O")
            if self.chk_version.isChecked():
                args.append(f"-sV")
                args.append(f"--version-intensity")
                args.append(str(self.version_intensity.value()))

        # Timing
        t_index = self.timing_combo.currentIndex()
        args.append(f"-T{t_index}")

        if self.max_retries.value() != 3:
            args += ["--max-retries", str(self.max_retries.value())]

        # Puertos
        mode = self.port_mode.currentIndex()
        if mode == 1:
            args.append("-p-")
        elif mode == 2:
            args += ["--top-ports", "100"]
        elif mode == 3 and self.port_custom.text().strip():
            args += ["-p", self.port_custom.text().strip()]

        if self.chk_fast.isChecked() and mode not in (1, 2):
            args.append("-F")

        # Verbose y opciones informativas
        if self.chk_verbose.isChecked():
            args.append("-v")
        if self.chk_reason.isChecked():
            args.append("--reason")
        if self.chk_tracert.isChecked():
            args.append("--traceroute")
        if self.chk_ipv6.isChecked():
            args.append("-6")

        # Scripts NSE
        if self.chk_default_scripts.isChecked():
            args.append("-sC")
        preset = self.script_combo.currentData()
        if preset:
            args += ["--script", preset]
        if self.custom_script.text().strip():
            args += ["--script", self.custom_script.text().strip()]

        # Salida a fichero — siempre guardamos XML para parsear resultados
        base = self.output_name.text().strip() or "scan_result"
        args += ["-oX", f"exports/{base}.xml"]
        if self.chk_save_txt.isChecked():
            args += ["-oN", f"exports/{base}.txt"]
        if self.chk_save_json.isChecked():
            args += ["-oG", f"exports/{base}.gnmap"]

        # Excluir hosts
        if self.chk_exclude.isChecked() and self.exclude_input.text().strip():
            args += ["--exclude", self.exclude_input.text().strip()]

        # Args extra libres
        if self.extra_args.text().strip():
            args += self.extra_args.text().strip().split()

        # Target al final
        target = self.target_input.text().strip()
        if target:
            args.append(target)

        self.command_changed.emit(args)

    def get_command(self) -> list[str]:
        """Devuelve el comando actual como lista de strings."""
        checked_btn = self._scan_group.checkedButton()
        self._rebuild_command()
        # Recuperar lo emitido en el último rebuild
        result = []
        self._last_command = result
        return result
