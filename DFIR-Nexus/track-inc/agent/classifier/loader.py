"""
Carga las reglas de clasificación desde un fichero YAML declarativo
(ver `rules.yaml`) y las convierte en instancias de `Rule`.

Objetivo: que el equipo pueda ajustar criticidades, añadir reglas nuevas
o inyectar IOCs (p. ej. desde el Módulo 2) SIN tocar código Python, y que
cualquier error en el YAML falle de forma clara y explícita en el
arranque del agente (fail-fast) en vez de fallar en silencio en medio de
una investigación.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agent.evidence.models import Criticality

from .engine import Rule


_RE_MITRE = re.compile(r"^T\d{4}(\.\d{3})?$")


class RulesConfigError(Exception):
    """Error de formato o contenido en rules.yaml. Mensaje siempre
    incluye qué regla y qué campo falló, para depurar rápido."""


def _parse_criticality(value: str, rule_name: str) -> Criticality:
    try:
        return Criticality(value)
    except ValueError as e:
        valid = ", ".join(c.value for c in Criticality)
        raise RulesConfigError(
            f"Regla '{rule_name}': criticidad '{value}' inválida. Valores válidos: {valid}."
        ) from e


def _parse_rule(raw: dict[str, Any], index: int) -> Rule:
    missing = [f for f in ("name", "criticality", "conditions") if f not in raw]
    if missing:
        raise RulesConfigError(
            f"Regla #{index} incompleta: faltan campos {missing}. Cada regla necesita "
            f"'name', 'criticality' y 'conditions'."
        )

    name = raw["name"]
    if not isinstance(raw["conditions"], dict) or not raw["conditions"]:
        raise RulesConfigError(f"Regla '{name}': 'conditions' debe ser un diccionario no vacío.")

    criticality = _parse_criticality(raw["criticality"], name)

    mitre = raw.get("mitre", [])
    if not isinstance(mitre, list) or not all(isinstance(t, str) and _RE_MITRE.match(t) for t in mitre):
        raise RulesConfigError(
            f"Regla '{name}': 'mitre' debe ser una lista de técnicas ATT&CK como T1059 o T1059.001."
        )

    # 'descripcion' y 'mitre' son opcionales: sin ellos, la regla funciona igual.
    try:
        return Rule(
            name=name,
            criticality=criticality,
            conditions=raw["conditions"],
            descripcion=raw.get("descripcion"),
            mitre=mitre,
        )
    except re.error as e:
        raise RulesConfigError(f"Regla '{name}': expresión regular 're:' no válida: {e}") from e


def load_rules_from_yaml(path: str | Path) -> tuple[list[Rule], Criticality]:
    """
    Devuelve (reglas_en_orden, criticidad_por_defecto).
    Lanza RulesConfigError con un mensaje accionable ante cualquier
    problema (fichero ausente, YAML mal formado, regla incompleta,
    nombres de regla duplicados, criticidad desconocida...).
    """
    path = Path(path)
    if not path.exists():
        raise RulesConfigError(f"No se encontró el fichero de reglas: {path}")

    try:
        # utf-8 explícito: sin él, en Windows se leía como cp1252 y una "Á" en
        # una descripción tumbaba el análisis entero con UnicodeDecodeError.
        raw_config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise RulesConfigError(f"El fichero {path} no es un YAML válido: {e}") from e

    if not raw_config or "rules" not in raw_config:
        raise RulesConfigError(f"El fichero {path} debe tener una clave de nivel superior 'rules'.")

    raw_rules = raw_config["rules"]
    if not isinstance(raw_rules, list) or len(raw_rules) == 0:
        raise RulesConfigError(f"'rules' en {path} debe ser una lista no vacía.")

    rules: list[Rule] = []
    seen_names: set[str] = set()
    for index, raw_rule in enumerate(raw_rules):
        rule = _parse_rule(raw_rule, index)
        if rule.name in seen_names:
            raise RulesConfigError(f"Nombre de regla duplicado: '{rule.name}'. Los nombres deben ser únicos.")
        seen_names.add(rule.name)
        rules.append(rule)

    default_raw = raw_config.get("default_criticality", Criticality.LOW.value)
    default_criticality = _parse_criticality(default_raw, "default_criticality")

    return rules, default_criticality
