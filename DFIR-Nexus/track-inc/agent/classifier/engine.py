"""
Clasificador de criticidad basado en reglas.

Las reglas son declarativas (lista de dicts, normalmente cargadas desde
YAML) para que sean auditables y ajustables sin tocar código. Cada regla
define condiciones simples sobre el RawEvent. Se evalúan TODAS y gana la
de mayor criticidad (a igualdad, la primera en el fichero). Si ninguna
regla aplica, se asigna la criticidad por defecto (LOW).

Antes ganaba la primera que casaba: `net user x /add & certutil -urlcache …`
salía ALTA (cuenta modificada) en vez de CRÍTICA (descarga), solo porque la
regla de cuentas estaba antes en el YAML.

Las condiciones de lista admiten dos tipos de candidato:

  - Subcadena: `"net user"`.
  - Expresión regular, con el prefijo `re:`: `"re:\\bsc(\\.exe)?\\s+create\\b"`.
    Permite exigir límites de palabra (que `misc create` no sea `sc create`)
    o variantes (`-e`, `-ec`, `-enc`… de PowerShell).

Ambos se comparan contra el texto NORMALIZADO (ver `normalizar`), que
neutraliza las ofuscaciones más baratas: `n^et user`, `"net" user`,
`net  user`, `i`e`x`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agent.evidence.models import Criticality, RawEvent

_PESO = {Criticality.LOW: 0, Criticality.MEDIUM: 1, Criticality.HIGH: 2, Criticality.CRITICAL: 3}
_RE_COMILLAS_Y_ESCAPES = re.compile(r"[\"'`^]")
_RE_ESPACIOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Forma canónica para comparar un comando con las reglas.

    Minúsculas; sin `^` (escape de cmd), comillas ni acento grave (escape de
    PowerShell), que el intérprete ignora pero rompían la comparación literal;
    y espacios en blanco (tabuladores incluidos) reducidos a uno. Se añade un
    espacio al final para que candidatos como `"-enc "` casen también al final
    de la línea.
    """
    sin_escapes = _RE_COMILLAS_Y_ESCAPES.sub("", texto.lower())
    return _RE_ESPACIOS.sub(" ", sin_escapes).strip() + " "


class _Candidatos:
    """Los candidatos de una condición, fundidos en UNA expresión regular.

    Una sola búsqueda por condición en lugar de una por candidato: con
    decenas de reglas y miles de líneas, el bucle en Python sobre cada
    subcadena y patrón era la mayor parte del tiempo de un análisis.
    """

    def __init__(self, valores: list[Any]):
        partes: list[str] = []
        for valor in valores:
            texto = str(valor)
            if texto.startswith("re:"):
                re.compile(texto[3:])  # valida cada patrón por separado: el error señala el culpable
                partes.append(f"(?:{texto[3:]})")
            else:
                subcadena = normalizar(texto).rstrip(" ") + (" " if texto.endswith(" ") else "")
                partes.append(re.escape(subcadena))
        self._patron = re.compile("|".join(partes)) if partes else None

    def casa(self, texto_normalizado: str) -> bool:
        return self._patron is not None and self._patron.search(texto_normalizado) is not None


class Rule:
    def __init__(
        self,
        name: str,
        criticality: Criticality,
        conditions: dict[str, Any],
        descripcion: str | None = None,
        mitre: list[str] | None = None,
    ):
        self.name = name
        self.criticality = criticality
        self.conditions = conditions
        # Texto opcional que explica al analista por que este patron es
        # sospechoso. Se muestra en el detalle del evento (Modulo 3); no
        # interviene en la clasificacion.
        self.descripcion = descripcion
        # Técnicas MITRE ATT&CK que representa la regla (p. ej. T1059.001).
        self.mitre = list(mitre or [])
        # Se compilan una vez: antes cada comparación volvía a pasar a
        # minúsculas todos los candidatos. Lanza re.error si un `re:` no es
        # una expresión válida (el loader lo convierte en RulesConfigError).
        # Condiciones preparadas una vez: ruta ya partida, candidatos ya
        # compilados, y las de valor exacto (source, event_type) delante, que
        # descartan la regla sin llegar a buscar en el texto.
        self._exactas = [
            (campo.split("."), valor) for campo, valor in conditions.items() if not isinstance(valor, list)
        ]
        self._de_lista = [
            (campo, campo.split("."), _Candidatos(valor))
            for campo, valor in conditions.items()
            if isinstance(valor, list)
        ]

    def matches(self, event: RawEvent) -> bool:
        return self.matches_dict(event.model_dump(), {})

    def matches_dict(self, datos: dict[str, Any], normalizados: dict[str, str]) -> bool:
        """Como `matches`, sobre el evento ya convertido a dict.

        `normalizados` es una caché de textos normalizados por campo que el
        motor comparte entre todas las reglas de un mismo evento: antes cada
        condición de cada regla volvía a serializar el evento entero
        (`model_dump`), y era más de la mitad del tiempo de un análisis.
        """
        for partes, esperado in self._exactas:
            if self._resolve(datos, partes) != esperado:
                return False
        for campo, partes, candidatos in self._de_lista:
            if campo not in normalizados:
                actual = self._resolve(datos, partes)
                normalizados[campo] = "" if actual is None else normalizar(str(actual))
            if not normalizados[campo] or not candidatos.casa(normalizados[campo]):
                return False
        return True

    @staticmethod
    def _resolve(datos: dict[str, Any], partes: list[str]) -> Any:
        """Resuelve rutas tipo 'payload.path' o 'event_type' sobre el evento."""
        current: Any = datos
        for part in partes:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


@dataclass
class Clasificacion:
    """Resultado completo: la regla que decide la criticidad y todas las que casaron."""

    criticality: Criticality
    regla: Rule | None
    reglas: list[Rule]


DEFAULT_RULES: list[Rule] = [
    Rule(
        name="borrado_de_logs",
        criticality=Criticality.CRITICAL,
        conditions={"source": "filesystem", "event_type": "deleted", "payload.path": ["/var/log", "\\logs\\", "eventlog"]},
    ),
    Rule(
        name="modificacion_binario_sistema",
        criticality=Criticality.CRITICAL,
        conditions={"source": "filesystem", "event_type": "modified", "payload.path": ["/bin/", "/usr/bin/", "system32"]},
    ),
    Rule(
        name="ejecucion_desde_temporal",
        criticality=Criticality.HIGH,
        conditions={"source": "process", "event_type": "exec", "payload.path": ["/tmp/", "\\temp\\", "\\appdata\\local\\temp"]},
    ),
    Rule(
        name="conexion_saliente_sospechosa",
        criticality=Criticality.HIGH,
        conditions={"source": "network", "event_type": "connection", "payload.flagged": True},
    ),
    Rule(
        name="cambio_permisos",
        criticality=Criticality.MEDIUM,
        conditions={"source": "filesystem", "event_type": "permission_changed"},
    ),
    # --- Reglas para logs de comandos (CU-03: Módulo 3 / Tracking) ---
    Rule(
        name="borrado_evidencias_o_shadow_copies",
        criticality=Criticality.CRITICAL,
        conditions={"source": "log", "payload.command": [
            "vssadmin delete shadows", "wevtutil cl", "clear-eventlog", "wbadmin delete",
        ]},
    ),
    Rule(
        name="powershell_ofuscado_o_descarga_remota",
        criticality=Criticality.CRITICAL,
        conditions={"source": "log", "payload.command": [
            "-enc ", "-encodedcommand", "downloadstring", "iex(", "invoke-expression",
        ]},
    ),
    Rule(
        name="herramienta_post_explotacion",
        criticality=Criticality.CRITICAL,
        conditions={"source": "log", "payload.command": [
            "mimikatz", "psexec", "cobalt", "invoke-mimikatz",
        ]},
    ),
    Rule(
        name="cuenta_o_grupo_modificado",
        criticality=Criticality.HIGH,
        conditions={"source": "log", "payload.command": [
            "net user", "net localgroup", "net group",
        ]},
    ),
    Rule(
        name="enumeracion_de_privilegios",
        criticality=Criticality.MEDIUM,
        conditions={"source": "log", "payload.command": [
            "whoami /priv", "whoami /all", "net accounts",
        ]},
    ),
]


class ClassifierEngine:
    def __init__(self, rules: list[Rule] | None = None, default: Criticality = Criticality.LOW):
        self.rules = rules if rules is not None else DEFAULT_RULES
        self.default = default

    @classmethod
    def from_yaml(cls, path) -> "ClassifierEngine":
        """Construye el motor cargando reglas desde un fichero YAML
        (ver agent/classifier/rules.yaml). Falla rápido y con un mensaje
        claro (RulesConfigError) si el fichero tiene algún problema."""
        from .loader import load_rules_from_yaml  # import local: evita ciclo engine<->loader

        rules, default_criticality = load_rules_from_yaml(path)
        return cls(rules=rules, default=default_criticality)

    def classify_detallado(self, event: RawEvent) -> Clasificacion:
        """Evalúa todas las reglas: la de mayor criticidad decide (a igualdad,
        la primera del fichero) y se devuelven también las demás que casaron."""
        datos = event.model_dump()
        normalizados: dict[str, str] = {}
        casadas = [rule for rule in self.rules if rule.matches_dict(datos, normalizados)]
        if not casadas:
            return Clasificacion(self.default, None, [])
        # max() devuelve la primera de las de peso máximo: respeta el orden del YAML
        principal = max(casadas, key=lambda r: _PESO[r.criticality])
        return Clasificacion(principal.criticality, principal, casadas)

    def combinar(self, *resultados: Clasificacion) -> Clasificacion:
        """Une varias clasificaciones del mismo evento (p. ej. el comando y
        su versión decodificada): todas las reglas, sin repetir, y decide la
        más grave."""
        casadas: dict[str, Rule] = {}
        for resultado in resultados:
            for regla in resultado.reglas:
                casadas.setdefault(regla.name, regla)
        if not casadas:
            return Clasificacion(self.default, None, [])
        lista = list(casadas.values())
        principal = max(lista, key=lambda r: _PESO[r.criticality])
        return Clasificacion(principal.criticality, principal, lista)

    def classify(self, event: RawEvent) -> tuple[Criticality, str | None]:
        """Devuelve (criticidad, nombre_de_la_regla_más_grave | None)."""
        resultado = self.classify_detallado(event)
        return resultado.criticality, resultado.regla.name if resultado.regla else None
