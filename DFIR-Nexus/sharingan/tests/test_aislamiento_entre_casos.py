"""
El asistente no puede mezclar dos casos, ni siquiera a través del historial.

El aislamiento entre casos es la promesa central del módulo de chat: cada
respuesta se apoya solo en el expediente del caso seleccionado. `context.py` lo
garantiza para las **consultas** —no existe forma de leer una fila de otro
caso—, pero quedaba una vía abierta por detrás: la conversación anterior se le
reenvía al modelo en cada turno, y la mantiene el cliente.

El fallo era real y se reprodujo antes de arreglarlo: preguntando por el caso 8
y cambiando el desplegable al caso 1 sin limpiar, el prompt del caso 1 contenía
`203.0.113.45`, `srv-preprod-01` y `auth.log`, que son del 8.
"""
from unittest.mock import patch

import pytest

from app.modules.chat import service
from app.modules.chat.schemas import Mensaje

#: Un turno anterior que habla de otro caso, con datos reconocibles.
HISTORIAL_AJENO = [
    Mensaje(rol="usuario", contenido="Que ocurrio en este caso?"),
    Mensaje(
        rol="asistente",
        contenido="Escaneo desde 203.0.113.45 contra srv-preprod-01, root en auth.log.",
    ),
]

DATOS_AJENOS = ("203.0.113.45", "srv-preprod-01", "auth.log")


def _texto_del_prompt(prep) -> str:
    return prep.sistema + "\n" + "\n".join(m["content"] for m in prep.mensajes)


def test_el_historial_de_otro_caso_no_entra_en_el_prompt(case_con_timeline, db_session):
    prep = service._preparar(
        db_session,
        "Y ahora que?",
        case_id=case_con_timeline.id,
        historial=HISTORIAL_AJENO,
        historial_case_id=case_con_timeline.id + 1000,  # otro caso cualquiera
    )
    texto = _texto_del_prompt(prep)

    for dato in DATOS_AJENOS:
        assert dato not in texto, f"«{dato}» se ha filtrado desde otro caso"


def test_descartar_el_historial_ajeno_se_avisa(case_con_timeline, db_session):
    """
    Descartarlo en silencio sería casi tan malo como no descartarlo: el perito
    creería que el asistente recuerda la conversación y no la recuerda.
    """
    prep = service._preparar(
        db_session,
        "Y ahora que?",
        case_id=case_con_timeline.id,
        historial=HISTORIAL_AJENO,
        historial_case_id=999,
    )
    assert prep.avisos_previos
    assert "otro caso" in prep.avisos_previos[0]


def test_el_aviso_llega_hasta_la_respuesta(case_con_timeline, db_session):
    """El aviso no sirve de nada si se queda dentro del servidor."""
    from app.modules.chat import llm

    salida = llm.Salida(texto="No consta.", modelo="prueba/modelo")
    with patch("app.modules.chat.llm.generar", return_value=salida):
        respuesta = service.responder(
            db_session,
            "Y ahora que?",
            case_id=case_con_timeline.id,
            historial=HISTORIAL_AJENO,
            historial_case_id=999,
        )

    assert any("otro caso" in a for a in respuesta.advertencias)


def test_el_historial_del_mismo_caso_si_se_conserva(case_con_timeline, db_session):
    """
    La regla acota, no rompe: dentro del mismo caso la conversación continúa.
    Sin esto, el arreglo habría dejado el chat sin memoria.
    """
    prep = service._preparar(
        db_session,
        "Y ahora que?",
        case_id=case_con_timeline.id,
        historial=HISTORIAL_AJENO,
        historial_case_id=case_con_timeline.id,
    )
    assert "203.0.113.45" in _texto_del_prompt(prep)


def test_sin_declarar_el_caso_del_historial_se_conserva(case_con_timeline, db_session):
    """
    `historial_case_id=None` significa «es del mismo caso», que es lo que
    asumían los clientes anteriores a este campo. Cambiar ese comportamiento
    por defecto rompería a cualquiera que no se haya actualizado.
    """
    prep = service._preparar(
        db_session,
        "Y ahora que?",
        case_id=case_con_timeline.id,
        historial=HISTORIAL_AJENO,
        historial_case_id=None,
    )
    assert "203.0.113.45" in _texto_del_prompt(prep)


@pytest.mark.parametrize("desde, hacia", [(8, None), (None, 8)])
def test_cambiar_entre_caso_y_consulta_general_tambien_descarta(
    desde, hacia, case_con_timeline, db_session
):
    """
    Los dos sentidos importan. De caso a general, el expediente se colaría en
    una consulta que la interfaz presenta como «sin caso»; de general a caso,
    entra ruido que el asistente podría citar como si constara.
    """
    case_id = case_con_timeline.id if hacia is not None else None
    historial_case_id = case_con_timeline.id if desde is not None else None
    if case_id == historial_case_id:
        pytest.skip("no hay cambio de ámbito")

    prep = service._preparar(
        db_session,
        "Y ahora que?",
        case_id=case_id,
        historial=HISTORIAL_AJENO,
        historial_case_id=historial_case_id,
    )
    # De general (None) a caso no se puede distinguir de «mismo caso» con el
    # valor por defecto, así que solo se exige el descarte cuando el cliente
    # declara un caso de origen distinto.
    if historial_case_id is not None:
        assert prep.avisos_previos
        for dato in DATOS_AJENOS:
            assert dato not in _texto_del_prompt(prep)
