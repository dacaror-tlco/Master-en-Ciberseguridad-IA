import pytest

from app.modules.cases.models import EstadoCaso
from app.modules.cases.state_machine import InvalidStateTransitionError, validar_transicion

TRANSICIONES_VALIDAS = [
    (EstadoCaso.ABIERTO, EstadoCaso.EN_PROGRESO),
    (EstadoCaso.ABIERTO, EstadoCaso.CERRADO),
    (EstadoCaso.ABIERTO, EstadoCaso.ARCHIVADO),
    (EstadoCaso.EN_PROGRESO, EstadoCaso.ABIERTO),
    (EstadoCaso.EN_PROGRESO, EstadoCaso.CERRADO),
    (EstadoCaso.CERRADO, EstadoCaso.EN_PROGRESO),
    (EstadoCaso.CERRADO, EstadoCaso.ARCHIVADO),
]

TRANSICIONES_INVALIDAS = [
    (EstadoCaso.EN_PROGRESO, EstadoCaso.ARCHIVADO),
    (EstadoCaso.CERRADO, EstadoCaso.ABIERTO),
    (EstadoCaso.ARCHIVADO, EstadoCaso.ABIERTO),
    (EstadoCaso.ARCHIVADO, EstadoCaso.EN_PROGRESO),
    (EstadoCaso.ARCHIVADO, EstadoCaso.CERRADO),
]


@pytest.mark.parametrize("actual,nuevo", TRANSICIONES_VALIDAS)
def test_transiciones_validas_no_lanzan(actual, nuevo):
    validar_transicion(actual, nuevo)


@pytest.mark.parametrize("actual,nuevo", TRANSICIONES_INVALIDAS)
def test_transiciones_invalidas_lanzan(actual, nuevo):
    with pytest.raises(InvalidStateTransitionError):
        validar_transicion(actual, nuevo)


@pytest.mark.parametrize("estado", list(EstadoCaso))
def test_transicion_al_mismo_estado_nunca_lanza(estado):
    validar_transicion(estado, estado)


def test_archivado_es_terminal():
    assert validar_transicion(EstadoCaso.ARCHIVADO, EstadoCaso.ARCHIVADO) is None
    for destino in EstadoCaso:
        if destino is EstadoCaso.ARCHIVADO:
            continue
        with pytest.raises(InvalidStateTransitionError):
            validar_transicion(EstadoCaso.ARCHIVADO, destino)
