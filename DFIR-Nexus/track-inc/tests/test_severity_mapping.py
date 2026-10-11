import pytest

from agent.evidence.models import Criticality
from app.modules.tracking.models import Severidad
from app.modules.tracking.severity_mapping import (
    criticality_to_severidad,
    severidad_to_criticality,
)


@pytest.mark.parametrize("criticality,expected", [
    (Criticality.LOW, Severidad.BAJA),
    (Criticality.MEDIUM, Severidad.MEDIA),
    (Criticality.HIGH, Severidad.ALTA),
    (Criticality.CRITICAL, Severidad.CRITICA),
])
def test_criticality_to_severidad(criticality, expected):
    assert criticality_to_severidad(criticality) == expected


@pytest.mark.parametrize("severidad,expected", [
    (Severidad.BAJA, Criticality.LOW),
    (Severidad.MEDIA, Criticality.MEDIUM),
    (Severidad.ALTA, Criticality.HIGH),
    (Severidad.CRITICA, Criticality.CRITICAL),
])
def test_severidad_to_criticality(severidad, expected):
    assert severidad_to_criticality(severidad) == expected


def test_mapping_is_a_perfect_round_trip():
    for c in Criticality:
        assert severidad_to_criticality(criticality_to_severidad(c)) == c
