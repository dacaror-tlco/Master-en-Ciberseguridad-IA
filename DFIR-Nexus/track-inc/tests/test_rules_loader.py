import pytest

from agent.classifier.engine import ClassifierEngine
from agent.classifier.loader import RulesConfigError, load_rules_from_yaml
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent

HOST = HostInfo(agent_id="agent-001", hostname="test-host", os="linux")

VALID_YAML = """
rules:
  - name: borrado_de_logs
    criticality: CRITICAL
    conditions:
      source: filesystem
      event_type: deleted
      payload.path: ["/var/log"]
  - name: cambio_permisos
    criticality: MEDIUM
    conditions:
      source: filesystem
      event_type: permission_changed
default_criticality: LOW
"""


def test_load_valid_rules_file(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(VALID_YAML)

    rules, default = load_rules_from_yaml(rules_file)

    assert len(rules) == 2
    assert rules[0].name == "borrado_de_logs"
    assert rules[0].criticality == Criticality.CRITICAL
    assert default == Criticality.LOW


def test_loaded_rules_actually_classify_correctly(tmp_path):
    """No basta con parsear bien: las reglas cargadas desde YAML tienen
    que producir el mismo resultado que las reglas hardcodeadas."""
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(VALID_YAML)

    engine = ClassifierEngine.from_yaml(rules_file)
    event = RawEvent(
        source=EventSource.FILESYSTEM, event_type="deleted", host_info=HOST,
        payload={"path": "/var/log/auth.log"},
    )
    criticality, rule_name = engine.classify(event)

    assert criticality == Criticality.CRITICAL
    assert rule_name == "borrado_de_logs"


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(RulesConfigError, match="No se encontró"):
        load_rules_from_yaml(tmp_path / "no_existe.yaml")


def test_malformed_yaml_raises_clear_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("rules: [this is not: valid: yaml: at all")

    with pytest.raises(RulesConfigError, match="no es un YAML válido"):
        load_rules_from_yaml(rules_file)


def test_missing_rules_key_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("default_criticality: LOW\n")

    with pytest.raises(RulesConfigError, match="'rules'"):
        load_rules_from_yaml(rules_file)


def test_empty_rules_list_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("rules: []\n")

    with pytest.raises(RulesConfigError, match="lista no vacía"):
        load_rules_from_yaml(rules_file)


def test_rule_missing_required_field_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("""
rules:
  - name: regla_incompleta
    criticality: HIGH
""")
    with pytest.raises(RulesConfigError, match="faltan campos"):
        load_rules_from_yaml(rules_file)


def test_invalid_criticality_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("""
rules:
  - name: regla_mala
    criticality: SUPER_CRITICAL
    conditions:
      source: filesystem
""")
    with pytest.raises(RulesConfigError, match="criticidad 'SUPER_CRITICAL' inválida"):
        load_rules_from_yaml(rules_file)


def test_duplicate_rule_names_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("""
rules:
  - name: misma_regla
    criticality: LOW
    conditions:
      source: filesystem
  - name: misma_regla
    criticality: HIGH
    conditions:
      source: network
""")
    with pytest.raises(RulesConfigError, match="duplicado"):
        load_rules_from_yaml(rules_file)


def test_empty_conditions_raises_error(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("""
rules:
  - name: sin_condiciones
    criticality: LOW
    conditions: {}
""")
    with pytest.raises(RulesConfigError, match="diccionario no vacío"):
        load_rules_from_yaml(rules_file)


def test_real_rules_yaml_file_loads_correctly():
    """El fichero real del repo (agent/classifier/rules.yaml) también
    debe ser válido — esto detecta si alguien lo rompe sin querer."""
    from pathlib import Path
    real_path = Path(__file__).parent.parent / "agent" / "classifier" / "rules.yaml"

    rules, default = load_rules_from_yaml(real_path)
    assert default == Criticality.LOW

    # No se fija el número exacto de reglas a propósito: rules.yaml está
    # pensado para ampliarse sin tocar código, y un `== N` obligaría a
    # editar este test cada vez que alguien añade una regla. Lo que sí
    # debe cumplirse es que el fichero cargue y que sigan estando las
    # reglas de las que depende el Módulo 3 (CU-03).
    assert len(rules) >= 10
    nombres = {r.name for r in rules}
    for esperada in (
        "borrado_evidencias_o_shadow_copies",
        "powershell_ofuscado_o_descarga_remota",
        "cuenta_o_grupo_modificado",
        "enumeracion_de_privilegios",
    ):
        assert esperada in nombres, f"falta la regla {esperada} en rules.yaml"
