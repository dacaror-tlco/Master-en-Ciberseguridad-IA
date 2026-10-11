"""
Traduce entre los dos vocabularios de severidad que conviven en este
módulo:

  - `Criticality` (agent.evidence.models): interno, motor de
    clasificación + cadena de hashes. LOW/MEDIUM/HIGH/CRITICAL.
  - `Severidad` (app.modules.tracking.models): el que espera el
    esquema oficial de CLAUDE.md. baja/media/alta/critica.

Todo lo que cruza hacia el esquema oficial (tracking_events) usa
Severidad; todo lo que queda dentro del motor interno usa Criticality.
"""

from __future__ import annotations

from agent.evidence.models import Criticality

from .models import Severidad

_CRITICALITY_TO_SEVERIDAD = {
    Criticality.LOW: Severidad.BAJA,
    Criticality.MEDIUM: Severidad.MEDIA,
    Criticality.HIGH: Severidad.ALTA,
    Criticality.CRITICAL: Severidad.CRITICA,
}

_SEVERIDAD_TO_CRITICALITY = {v: k for k, v in _CRITICALITY_TO_SEVERIDAD.items()}


def criticality_to_severidad(criticality: Criticality) -> Severidad:
    return _CRITICALITY_TO_SEVERIDAD[criticality]


def severidad_to_criticality(severidad: Severidad) -> Criticality:
    return _SEVERIDAD_TO_CRITICALITY[severidad]
