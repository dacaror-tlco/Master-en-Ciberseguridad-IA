"""
Tests de la redacción del informe con modelo local (Ollama).

Nunca hay red: se mockea `llm.generar`, igual que la ruta de Anthropic mockea
su cliente. Lo que se comprueba aquí no es que el modelo escriba bien —eso no
se puede testear—, sino que **las garantías del informe son las mismas venga
de donde venga la narrativa**: citas verificadas, nada truncado, y el registro
diciendo qué modelo la escribió de verdad.
"""
from unittest.mock import patch

import pytest

from app.modules.chat import llm
from app.modules.reports import ai_narrative, repository


def _eventos(db_session, case):
    return repository.get_timeline_events(db_session, case.id)


def _json(hallazgos: list[tuple[str, list[int]]], conclusiones: str) -> str:
    """Respuesta del modelo local en su esquema: afirmación + eventos que la respaldan."""
    import json as _j

    return _j.dumps(
        {
            "hallazgos": [{"afirmacion": a, "eventos": e} for a, e in hallazgos],
            "conclusiones": conclusiones,
        }
    )


def _con_local(texto_json: str, truncada: bool = False):
    """Ejecuta la ruta local con una respuesta del modelo ya decidida."""
    salida = llm.Salida(
        texto=texto_json, modelo="ollama/qwen2.5:3b-instruct", truncada=truncada
    )
    return patch("app.modules.chat.llm.generar", return_value=salida)


def test_narrativa_local_no_necesita_api_key(case_con_timeline, db_session):
    """El motivo de existir de esta ruta: informes sin API de pago."""
    eventos = _eventos(db_session, case_con_timeline)
    with patch("app.core.config.settings.narrativa_provider", "ollama"), \
         patch("app.core.config.settings.anthropic_api_key", ""), \
         _con_local(_json([("Hubo un escaneo", [1])], "Intrusion.")):
        narrativa = ai_narrative.generar_narrativa(case_con_timeline, eventos)

    # El corchete lo pone el código, no el modelo: el modelo solo dijo «1».
    assert narrativa.hallazgos == "Hubo un escaneo. [E1]"
    assert narrativa.conclusiones == "Intrusion."


def test_el_informe_declara_el_modelo_local_que_lo_redacto(case_con_timeline, db_session):
    """
    El apartado 8 no puede seguir diciendo «claude-opus-5» cuando lo escribió
    un modelo de 3B en la máquina del perito.
    """
    eventos = _eventos(db_session, case_con_timeline)
    with patch("app.core.config.settings.narrativa_provider", "ollama"), \
         _con_local(_json([("Escaneo", [1])], "X.")):
        narrativa = ai_narrative.generar_narrativa(case_con_timeline, eventos)

    assert narrativa.modelo == "ollama/qwen2.5:3b-instruct"
    assert narrativa.modelo != ai_narrative.MODEL
    # Y el registro archivado tiene que decir lo mismo que la portada.
    assert "modelo: ollama/qwen2.5:3b-instruct" in narrativa.prompt


def test_narrativa_local_truncada_no_se_firma(case_con_timeline, db_session):
    """Misma regla que con Anthropic: un informe no se firma a medias."""
    eventos = _eventos(db_session, case_con_timeline)
    with patch("app.core.config.settings.narrativa_provider", "ollama"), \
         _con_local(_json([("Escaneo", [1])], "X."), truncada=True):
        with pytest.raises(ai_narrative.AIResponseError, match="truncado"):
            ai_narrative.generar_narrativa(case_con_timeline, eventos)


def test_narrativa_local_con_cita_inexistente_se_rechaza(case_con_timeline, db_session):
    eventos = _eventos(db_session, case_con_timeline)
    with patch("app.core.config.settings.narrativa_provider", "ollama"), \
         _con_local(_json([("Algo", [99])], "X.")):
        with pytest.raises(ai_narrative.AIResponseError, match=r"\[E99\]"):
            ai_narrative.generar_narrativa(case_con_timeline, eventos)


def test_hallazgo_sin_evento_que_lo_respalde_se_rechaza(case_con_timeline, db_session):
    """
    El fallo real que motivó todo esto: la primera narrativa generada con el
    modelo local salió coherente y **sin una sola referencia**, y pasaba el
    filtro porque solo se comprobaba que las citas presentes fuesen válidas.

    Hoy el esquema obliga a que cada afirmación traiga sus eventos, pero un
    modelo puede devolver la lista vacía igualmente: entonces se rechaza.
    """
    eventos = _eventos(db_session, case_con_timeline)
    assert eventos, "la fixture debe tener cronología para que la regla aplique"

    with patch("app.core.config.settings.narrativa_provider", "ollama"), \
         _con_local(_json([("Hubo una intrusion", [])], "X.")):
        with pytest.raises(ai_narrative.AIResponseError, match="sin ningún evento"):
            ai_narrative.generar_narrativa(case_con_timeline, eventos)


def test_la_regla_de_citas_tambien_rige_para_anthropic(case_con_timeline, db_session):
    """
    No es una salvaguarda «del modelo local»: es una propiedad del informe.
    Si Claude dejara de citar, tampoco debería firmarse.
    """
    import json
    from types import SimpleNamespace

    eventos = _eventos(db_session, case_con_timeline)
    respuesta = SimpleNamespace(
        stop_reason="end_turn",
        content=[
            SimpleNamespace(
                type="text",
                text=json.dumps({"hallazgos": "Hubo una intrusion.", "conclusiones": "X."}),
            )
        ],
    )
    cliente = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: respuesta))
    with patch("app.core.config.settings.anthropic_api_key", "clave-de-prueba"), \
         patch("app.modules.reports.ai_narrative.Anthropic", return_value=cliente):
        with pytest.raises(ai_narrative.AIResponseError, match="no cita"):
            ai_narrative.generar_narrativa(case_con_timeline, eventos)


def test_el_prompt_recuerda_el_rango_de_citas_disponible(case_con_timeline, db_session):
    """
    El recordatorio final del prompt existe porque un modelo pequeño atiende a
    lo último que lee. Si desaparece, la ruta local vuelve a no citar.
    """
    eventos = _eventos(db_session, case_con_timeline)
    prompt = ai_narrative._build_prompt(case_con_timeline, eventos, notas=None)

    assert "RECUERDA" in prompt
    assert f"[E{len(eventos)}]" in prompt
