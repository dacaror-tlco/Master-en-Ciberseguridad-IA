"""
Archivo de las instrucciones enviadas a la IA.

El apartado 8 del informe declara con qué modelo y con qué versión de
instrucciones se redactó. Hasta ahora eso había que creérselo: la versión es
una etiqueta, y el texto al que apunta vive en el código, que cambia. Guardar
la transcripción literal junto al informe es lo que convierte esa declaración
en algo contrastable.
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.modules.reports import ai_narrative, document, repository, service
from tests.conftest import NARRATIVA_FALSA, documento_de_prueba


def _narrativa_con_prompt(db_session, caso):
    """La narrativa tal y como sale de una llamada real, con su transcripción."""
    eventos = repository.get_timeline_events(db_session, caso.id)
    respuesta = SimpleNamespace(
        stop_reason="end_turn",
        content=[
            SimpleNamespace(
                type="text",
                text=json.dumps(
                    {"hallazgos": "Se observa el evento [E1].", "conclusiones": "Acreditado."}
                ),
            )
        ],
    )
    cliente = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: respuesta))
    with patch("app.core.config.settings.anthropic_api_key", "clave-de-prueba"), \
         patch("app.modules.reports.ai_narrative.Anthropic", return_value=cliente):
        return ai_narrative.generar_narrativa(caso, eventos, notas="Revisar el vector de entrada")


def _generar(db_session, caso, narrativa):
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=narrativa
    ):
        return service.generate_report(db_session, case_id=caso.id, generado_por="Tester")


# --- Qué se archiva ----------------------------------------------------------


def test_la_transcripcion_recoge_lo_que_de_verdad_se_envio(db_session, case_con_timeline):
    """
    Los parámetros van con los prompts porque el texto por sí solo no explica
    la salida: el mismo prompt con otro `effort` no produce lo mismo.
    """
    narrativa = _narrativa_con_prompt(db_session, case_con_timeline)

    assert ai_narrative._SYSTEM_PROMPT in narrativa.prompt
    assert f"modelo: {ai_narrative.MODEL}" in narrativa.prompt
    assert f"version_prompt: {ai_narrative.PROMPT_VERSION}" in narrativa.prompt
    # La cronología concreta que se le pasó, que es lo que cambia en cada informe.
    assert "[E1]" in narrativa.prompt
    assert "Revisar el vector de entrada" in narrativa.prompt


def test_se_archiva_junto_a_las_copias_y_con_su_huella(
    db_session, case_con_timeline, storage_dir
):
    narrativa = _narrativa_con_prompt(db_session, case_con_timeline)
    report = _generar(db_session, case_con_timeline, narrativa)

    ruta = storage_dir / f"case_{case_con_timeline.id}" / "report_v1.prompt.txt"
    assert ruta.is_file()
    assert ruta.read_text(encoding="utf-8") == narrativa.prompt
    assert service.CLAVE_PROMPT in report.huellas


def test_se_recupera_por_su_endpoint(client, case_con_timeline, storage_dir, db_session):
    narrativa = _narrativa_con_prompt(db_session, case_con_timeline)
    report = _generar(db_session, case_con_timeline, narrativa)

    respuesta = client.get(f"/reports/{report.id}/prompt")

    assert respuesta.status_code == 200
    assert respuesta.text == narrativa.prompt
    assert respuesta.headers["X-Informe-SHA256"] == report.huellas[service.CLAVE_PROMPT]


def test_una_transcripcion_alterada_no_se_sirve(
    db_session, case_con_timeline, storage_dir
):
    """
    Se le exige la misma integridad que a las copias del informe: una
    transcripción que se pueda editar después no prueba nada.
    """
    narrativa = _narrativa_con_prompt(db_session, case_con_timeline)
    report = _generar(db_session, case_con_timeline, narrativa)
    service._ruta_prompt(report.archivo_pdf).write_text("otras instrucciones", encoding="utf-8")

    with pytest.raises(service.ReportTamperedError):
        service.get_report_prompt(db_session, report.id)


def test_un_informe_sin_transcripcion_devuelve_410(
    client, case_con_timeline, storage_dir, db_session
):
    """
    Los informes anteriores a esto no la tienen. No se reconstruye ahora: el
    prompt que produciría el código de hoy no tiene por qué ser el que se usó.
    """
    report = _generar(db_session, case_con_timeline, NARRATIVA_FALSA)

    respuesta = client.get(f"/reports/{report.id}/prompt")

    assert respuesta.status_code == 410
    assert not service._ruta_prompt(report.archivo_pdf).exists()


# --- Lo que el informe declara ----------------------------------------------


def test_el_apartado_8_solo_promete_el_archivo_si_existe(db_session, case_con_timeline):
    """
    Una previsualización no llama a la IA y no archiva nada. Si el párrafo
    saliera igual, el documento estaría declarando un registro que no tiene.
    """
    con_prompt = documento_de_prueba(
        db_session,
        case_con_timeline,
        narrativa=ai_narrative.Narrativa(
            hallazgos="H [E1].", conclusiones="C.", prompt="lo que se envió"
        ),
    )
    sin_prompt = documento_de_prueba(db_session, case_con_timeline)

    def texto(doc):
        return " ".join(
            b.texto for b in doc.bloques if isinstance(b, document.Parrafo)
        )

    assert "quedan archivadas literalmente" in texto(con_prompt)
    assert "quedan archivadas literalmente" not in texto(sin_prompt)
