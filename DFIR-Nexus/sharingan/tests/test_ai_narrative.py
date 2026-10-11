"""
Tests de la capa de IA. Nunca hay red: se mockea el cliente de Anthropic y
se comprueba lo que el módulo hace con la respuesta.
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.modules.reports import ai_narrative


def _respuesta(payload: dict, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=json.dumps(payload))],
    )


def _llamar(case, eventos, respuesta):
    cliente = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kwargs: respuesta)
    )
    with patch("app.core.config.settings.anthropic_api_key", "clave-de-prueba"), \
         patch("app.modules.reports.ai_narrative.Anthropic", return_value=cliente):
        return ai_narrative.generar_narrativa(case, eventos)


def test_sin_api_key_lanza_error_explicito(case_con_timeline, db_session):
    from app.modules.reports import repository

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    with pytest.raises(ai_narrative.AIConfigError):
        ai_narrative.generar_narrativa(case_con_timeline, eventos)


def test_narrativa_valida(case_con_timeline, db_session):
    from app.modules.reports import repository

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    narrativa = _llamar(
        case_con_timeline,
        eventos,
        _respuesta({"hallazgos": "Ocurrió algo [E1].", "conclusiones": "Se concluye X."}),
    )

    assert narrativa.hallazgos == "Ocurrió algo [E1]."
    assert narrativa.modelo == ai_narrative.MODEL
    assert "HALLAZGOS" in narrativa.texto_plano


def test_respuesta_truncada_no_se_firma(case_con_timeline, db_session):
    """Unas conclusiones cortadas a mitad de frase no pueden acabar en un informe."""
    from app.modules.reports import repository

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    with pytest.raises(ai_narrative.AIResponseError, match="truncado"):
        _llamar(
            case_con_timeline,
            eventos,
            _respuesta({"hallazgos": "a", "conclusiones": "b"}, stop_reason="max_tokens"),
        )


def test_cita_a_un_evento_inexistente_se_rechaza(case_con_timeline, db_session):
    """La comprobación de alucinación: el caso tiene 3 eventos, [E9] no existe."""
    from app.modules.reports import repository

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    with pytest.raises(ai_narrative.AIResponseError, match=r"\[E9\]"):
        _llamar(
            case_con_timeline,
            eventos,
            _respuesta({"hallazgos": "Se detectó una intrusión [E9].", "conclusiones": "X."}),
        )


def test_error_de_red_se_traduce_a_ai_unavailable(case_con_timeline, db_session):
    import anthropic

    from app.modules.reports import repository

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)

    def _falla(**kwargs):
        raise anthropic.APIConnectionError(request=None)

    cliente = SimpleNamespace(messages=SimpleNamespace(create=_falla))
    with patch("app.core.config.settings.anthropic_api_key", "clave-de-prueba"), \
         patch("app.modules.reports.ai_narrative.Anthropic", return_value=cliente):
        with pytest.raises(ai_narrative.AIUnavailableError):
            ai_narrative.generar_narrativa(case_con_timeline, eventos)
