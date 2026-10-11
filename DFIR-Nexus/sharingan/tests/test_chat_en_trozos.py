"""
El streaming del asistente: mismo contrato con los dos proveedores.

Estaba sin cubrir, y era el hueco con más filo del módulo. `POST /chat/stream`
emite el texto en bruto según lo escribe el modelo y **al terminar lo sustituye**
por la versión verificada: si el elemento final se perdiera, en pantalla quedaría
el borrador sin comprobar —con sus citas inventadas intactas— y nada fallaría de
forma visible. Que la respuesta final del flujo esté verificada es exactamente
lo que estos tests fijan.

Nunca hay red: se mockea `llm.generar_en_trozos`, igual que el resto de la suite
mockea `llm.generar`.
"""
from unittest.mock import patch

from app.modules.chat import service
from app.modules.chat.llm import Salida


def _en_trozos(trozos, texto_final=None, *, modelo="test/fake", truncada=False):
    """Pone `trozos` en boca del modelo y cierra con su `Salida`, como el real."""
    completo = texto_final if texto_final is not None else "".join(trozos)

    def _falso(sistema, mensajes, num_predict=None, proveedor=None):
        for trozo in trozos:
            yield ("trozo", trozo)
        yield ("salida", Salida(texto=completo, modelo=modelo, truncada=truncada))

    return patch.object(service.llm, "generar_en_trozos", _falso)


def _recorrer(db_session, caso=None, mensaje="¿Qué pasó?"):
    return list(
        service.responder_en_trozos(
            db=db_session,
            mensaje=mensaje,
            case_id=caso.id if caso else None,
            historial=[],
            historial_case_id=caso.id if caso else None,
        )
    )


def test_los_trozos_llegan_y_el_ultimo_elemento_es_la_respuesta(case_con_anexos, db_session):
    with _en_trozos(["Se observa ", "un acceso ", "no autorizado."]):
        eventos = _recorrer(db_session, case_con_anexos)

    tipos = [tipo for tipo, _ in eventos]
    assert tipos == ["trozo", "trozo", "trozo", "fin"]
    assert [valor for tipo, valor in eventos if tipo == "trozo"] == [
        "Se observa ",
        "un acceso ",
        "no autorizado.",
    ]


def test_el_texto_final_esta_verificado_aunque_los_trozos_no(case_con_anexos, db_session):
    """
    El corazón del asunto: la cita inventada aparece en los trozos (son el texto
    en bruto del modelo) y **no** en la respuesta final. La interfaz se queda con
    la segunda.
    """
    trozos = ["Hubo un acceso ", "no autorizado [EV999]."]
    with _en_trozos(trozos):
        eventos = _recorrer(db_session, case_con_anexos)

    crudo = "".join(valor for tipo, valor in eventos if tipo == "trozo")
    assert "[EV999]" in crudo, "los trozos son el borrador: la cita falsa tiene que estar"

    _, respuesta = eventos[-1]
    assert "[EV999]" not in respuesta.texto
    assert "[sin respaldo]" in respuesta.texto
    assert any("sin respaldo" in aviso for aviso in respuesta.advertencias)


def test_una_cita_real_sobrevive_al_streaming(case_con_anexos, db_session):
    contexto = service._preparar(
        db_session, "¿Qué pasó?", case_con_anexos.id, historial=[], historial_case_id=None
    ).ctx
    ref = sorted(contexto.refs)[0]

    with _en_trozos([f"El hecho consta [{ref}]."]):
        eventos = _recorrer(db_session, case_con_anexos)

    _, respuesta = eventos[-1]
    assert f"[{ref}]" in respuesta.texto
    assert [f.ref for f in respuesta.fuentes] == [ref]


def test_el_modelo_declarado_es_el_que_dice_el_flujo(case_con_anexos, db_session):
    """
    No se supone por el proveedor configurado: lo dice la `Salida`. Importa
    porque el apartado del informe y la interfaz del chat declaran qué modelo
    respondió, y con dos proveedores en juego adivinarlo sería mentir la mitad
    de las veces.
    """
    with _en_trozos(["Respuesta."], modelo="anthropic/claude-opus-5"):
        _, respuesta = _recorrer(db_session, case_con_anexos)[-1]
    assert respuesta.modelo == "anthropic/claude-opus-5"


def test_una_respuesta_truncada_se_avisa(case_con_anexos, db_session):
    with _en_trozos(["Respuesta cortada a mit"], truncada=True):
        _, respuesta = _recorrer(db_session, case_con_anexos)[-1]
    assert respuesta.advertencias, "una respuesta truncada tiene que avisar"


def test_un_flujo_sin_elemento_final_es_un_error_y_no_una_respuesta_a_medias(
    case_con_anexos, db_session
):
    """
    Si el generador se corta sin emitir su `("salida", ...)`, lo que hay en
    pantalla es el borrador sin verificar. Devolverlo como bueno sería el peor
    fallo posible de este módulo, así que se convierte en error explícito.
    """

    def _cortado(sistema, mensajes, num_predict=None, proveedor=None):
        yield ("trozo", "Texto a medias [EV999]")

    with patch.object(service.llm, "generar_en_trozos", _cortado):
        generador = service.responder_en_trozos(
            db=db_session,
            mensaje="¿Qué pasó?",
            case_id=case_con_anexos.id,
            historial=[],
            historial_case_id=case_con_anexos.id,
        )
        try:
            list(generador)
        except service.ChatResponseError as exc:
            assert "sin respuesta completa" in str(exc)
        else:
            raise AssertionError("un flujo cortado tiene que dar ChatResponseError")


def test_el_caso_se_prepara_una_sola_vez(case_con_anexos, db_session):
    """
    Con Anthropic, el camino incremental llamaba antes a `responder()`, que
    rearmaba el expediente entero por segunda vez: dos veces las consultas de
    las seis tablas por cada pregunta. Al unificar el streaming dejó de pasar, y
    esto lo fija — es el tipo de coste que vuelve sin que nada falle.
    """
    with _en_trozos(["Respuesta."]), patch.object(
        service, "_preparar", wraps=service._preparar
    ) as espia:
        _recorrer(db_session, case_con_anexos)

    assert espia.call_count == 1
