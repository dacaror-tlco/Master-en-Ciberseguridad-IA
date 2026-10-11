"""
Ninguna cita que el asistente muestre puede ser inventada.

La regla del módulo: cada afirmación lleva la referencia de la fila de la que
sale (`[EV3]`, `[TR7]`…), y después se comprueba **contra el contexto que se le
dio**, no contra un patrón, que esa fila existiera. Lo que se hace con las que
no existen no es descartar la respuesta entera —suele tener partes útiles— sino
retirarlas del texto, sustituirlas por «[sin respaldo]» y devolver un aviso
visible. Esa es la diferencia con el informe pericial, donde una cita inválida
sí tumba la generación: el informe se firma y se entrega, la respuesta de chat
la relee una persona que puede descartarla.

Era la propiedad del asistente que quedaba sin test propio: estaban el
aislamiento entre casos (test_aislamiento_entre_casos.py), la regla de citas del
informe (test_narrativa_local.py) y la autenticación (test_auth_chat.py), pero
no esto — y es justo la que distingue «un modelo que habla de un caso» de «una
herramienta cuyo resultado se puede verificar fila a fila».
"""
from unittest.mock import patch

from app.modules.chat import service
from app.modules.chat.llm import Salida


def _respuesta_del_modelo(texto: str, db_session, caso=None, mensaje="¿Qué pasó?"):
    """Pone `texto` en boca del modelo y devuelve la respuesta ya verificada."""
    with patch.object(
        service.llm, "generar", return_value=Salida(texto=texto, modelo="test/fake", truncada=False)
    ):
        return service.responder(
            db=db_session,
            mensaje=mensaje,
            case_id=caso.id if caso else None,
            historial=[],
            historial_case_id=caso.id if caso else None,
        )


def test_una_cita_inventada_se_retira_del_texto(case_con_anexos, db_session):
    respuesta = _respuesta_del_modelo(
        "Hubo un acceso no autorizado [EV999] y después borrado de logs [TR888].",
        db_session,
        case_con_anexos,
    )

    assert "[EV999]" not in respuesta.texto
    assert "[TR888]" not in respuesta.texto
    assert "[sin respaldo]" in respuesta.texto


def test_retirarla_en_silencio_no_valdría(case_con_anexos, db_session):
    """
    Sustituir y callarse dejaría al analista leyendo un texto que parece
    respaldado. El aviso es parte de la garantía, no un extra.
    """
    respuesta = _respuesta_del_modelo(
        "Se observa un acceso desde una IP maliciosa [EV999].", db_session, case_con_anexos
    )

    assert respuesta.advertencias, "una cita inválida tiene que dejar aviso"
    assert any("sin respaldo" in aviso for aviso in respuesta.advertencias)


def test_una_cita_real_sobrevive_y_aparece_como_fuente(case_con_anexos, db_session):
    """
    El otro lado del contrato: si la fila existe, la cita se conserva **y** la
    fila viaja en `fuentes`, que es lo que permite al frontend enseñar de dónde
    sale cada cosa. Una verificación que retirase también las buenas cumpliría
    el test de arriba y dejaría el módulo inservible.
    """
    contexto = service._preparar(
        db_session, "¿Qué pasó?", case_con_anexos.id, historial=[], historial_case_id=None
    ).ctx
    assert contexto.refs, "el caso de prueba debería aportar filas citables"
    ref = sorted(contexto.refs)[0]

    respuesta = _respuesta_del_modelo(
        f"El hecho consta en el expediente [{ref}].", db_session, case_con_anexos
    )

    assert f"[{ref}]" in respuesta.texto
    assert [f.ref for f in respuesta.fuentes] == [ref]
    assert not any("sin respaldo" in aviso for aviso in respuesta.advertencias)


def test_solo_se_devuelven_como_fuente_las_filas_citadas(case_con_anexos, db_session):
    """
    `fuentes` es «de dónde sale lo que acabas de leer», no «todo lo que se le
    pasó al modelo». Si devolviese el expediente entero, el panel de fuentes
    dejaría de significar nada.
    """
    respuesta = _respuesta_del_modelo(
        "No puedo determinarlo con los datos disponibles.", db_session, case_con_anexos
    )

    assert respuesta.fuentes == []
    assert respuesta.filas_de_contexto > 0, "sí se le pasó contexto: simplemente no citó nada"


def test_sin_caso_cualquier_cita_es_inventada_por_definicion(db_session):
    """
    En una consulta general (sin `case_id`) no hay expediente, así que no hay
    ninguna fila que una cita pueda referenciar. El modelo local, entrenado a
    citar, las produce de todas formas.
    """
    respuesta = _respuesta_del_modelo(
        "La cadena de custodia documenta cada traspaso [EV1].",
        db_session,
        caso=None,
        mensaje="¿Qué es la cadena de custodia?",
    )

    assert "[EV1]" not in respuesta.texto
    assert "[sin respaldo]" in respuesta.texto
    assert respuesta.con_contexto_de_caso is False
