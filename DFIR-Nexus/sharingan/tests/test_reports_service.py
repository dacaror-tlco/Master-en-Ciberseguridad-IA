from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.reports import document, service
from app.modules.shared.models import Case, EstadoCaso
from tests.conftest import NARRATIVA_FALSA


def test_generate_report_case_inexistente(db_session, tmp_path):
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)):
        with pytest.raises(service.CaseNotFoundError):
            service.generate_report(db_session, case_id=999, generado_por="Tester")


def test_generate_report_sin_eventos(db_session, tmp_path):
    caso = Case(
        nombre="Caso vacío",
        estado=EstadoCaso.ABIERTO,
        fecha_creacion=datetime.now(timezone.utc),
    )
    db_session.add(caso)
    db_session.commit()
    db_session.refresh(caso)

    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)):
        with pytest.raises(service.EmptyTimelineError):
            service.generate_report(db_session, case_id=caso.id, generado_por="Tester")


def test_generate_report_ok_y_versiona(db_session, case_con_timeline, tmp_path):
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        reporte_1 = service.generate_report(
            db_session, case_id=case_con_timeline.id, generado_por="Tester"
        )
        reporte_2 = service.generate_report(
            db_session, case_id=case_con_timeline.id, generado_por="Tester"
        )

    assert reporte_1.version == 1
    assert reporte_2.version == 2
    assert "HALLAZGOS" in reporte_1.resumen_ia
    assert "CONCLUSIONES" in reporte_1.resumen_ia
    assert (tmp_path / f"case_{case_con_timeline.id}" / "report_v1.pdf").exists()
    assert (tmp_path / f"case_{case_con_timeline.id}" / "report_v2.pdf").exists()


def test_generate_report_persiste_las_notas_del_perito(db_session, case_con_timeline, tmp_path):
    """Las notas condicionan las conclusiones: sin registrarlas el informe no es reproducible."""
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        reporte = service.generate_report(
            db_session,
            case_id=case_con_timeline.id,
            generado_por="Tester",
            notas="Centrar el análisis en el vector de entrada.",
        )

    assert reporte.notas == "Centrar el análisis en el vector de entrada."


def _espia_documento(capturado):
    """
    Captura los argumentos con los que se compone el documento y deja pasar
    la llamada real: los renderizadores necesitan un `Documento` de verdad.
    """
    real = document.construir_documento

    def _captura(**kwargs):
        capturado.update(kwargs)
        return real(**kwargs)

    return patch(
        "app.modules.reports.document.construir_documento", side_effect=_captura
    )


def test_fecha_del_documento_y_del_registro_coinciden(db_session, case_con_timeline, tmp_path):
    """El sello del documento y el de su fila en BD tienen que ser el mismo."""
    capturado = {}

    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA), \
         _espia_documento(capturado):
        reporte = service.generate_report(
            db_session, case_id=case_con_timeline.id, generado_por="Tester"
        )

    # La columna es TIMESTAMP sin zona (tanto en MySQL como en SQLite), así que
    # al releer se pierde el tzinfo: lo que se compara es el instante, que es
    # justo lo que tiene que coincidir entre el documento y su registro.
    assert reporte.fecha_generacion.replace(tzinfo=None) == capturado[
        "generado_el"
    ].replace(tzinfo=None)


def test_generate_report_incluye_los_anexos(db_session, case_con_anexos, tmp_path):
    """El documento debe recibir evidencias, OSINT y tracking, no solo la cronología."""
    capturado = {}

    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA), \
         _espia_documento(capturado):
        service.generate_report(db_session, case_id=case_con_anexos.id, generado_por="Tester")

    assert len(capturado["evidences"]) == 1
    assert len(capturado["osint_results"]) == 1
    assert len(capturado["tracking_events"]) == 1


def test_get_report_file_detecta_pdf_borrado(db_session, case_con_timeline, tmp_path):
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        reporte = service.generate_report(
            db_session, case_id=case_con_timeline.id, generado_por="Tester"
        )

    (tmp_path / f"case_{case_con_timeline.id}" / "report_v1.pdf").unlink()

    with pytest.raises(service.ReportFileMissingError):
        service.get_report_file(db_session, reporte.id)
