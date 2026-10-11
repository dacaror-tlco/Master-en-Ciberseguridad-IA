"""
Máquina de estados de Case. Único lugar del proyecto donde se decide si una
transición de `estado` es válida — antes, un cambio de estado era un
`setattr` genérico sin ninguna restricción (repository.update_case).

Estados y transiciones (no se inventa ningún estado fuera de los cuatro que
ya define CLAUDE.md/EstadoCaso):

    ABIERTO ---------> EN_PROGRESO
       |                    |  ^
       |                    v  |
       +--------------> CERRADO <---+
       |                    |       |
       v                    v       |
    ARCHIVADO          ARCHIVADO ---+ (CERRADO <-> EN_PROGRESO: reapertura)

    ABIERTO      -> {EN_PROGRESO, CERRADO, ARCHIVADO}
    EN_PROGRESO  -> {ABIERTO, CERRADO}
    CERRADO      -> {EN_PROGRESO, ARCHIVADO}
    ARCHIVADO    -> {}  (terminal: un caso archivado es un registro
                         histórico cerrado; no cambia de estado ni de
                         contenido — ver service.update_case)
"""

from app.modules.cases.models import EstadoCaso

TRANSICIONES_VALIDAS: dict[EstadoCaso, frozenset[EstadoCaso]] = {
    EstadoCaso.ABIERTO: frozenset({EstadoCaso.EN_PROGRESO, EstadoCaso.CERRADO, EstadoCaso.ARCHIVADO}),
    EstadoCaso.EN_PROGRESO: frozenset({EstadoCaso.ABIERTO, EstadoCaso.CERRADO}),
    EstadoCaso.CERRADO: frozenset({EstadoCaso.EN_PROGRESO, EstadoCaso.ARCHIVADO}),
    EstadoCaso.ARCHIVADO: frozenset(),
}


class InvalidStateTransitionError(Exception):
    def __init__(self, actual: EstadoCaso, nuevo: EstadoCaso):
        self.actual = actual
        self.nuevo = nuevo
        super().__init__(f"Transición de estado inválida: {actual.value} -> {nuevo.value}")


def validar_transicion(actual: EstadoCaso, nuevo: EstadoCaso) -> None:
    """No-op si actual == nuevo (idempotente). Lanza si la transición no
    está en la tabla anterior."""
    if actual == nuevo:
        return
    if nuevo not in TRANSICIONES_VALIDAS.get(actual, frozenset()):
        raise InvalidStateTransitionError(actual, nuevo)
