"""
Tests de cómo se guarda y se localiza el informe emitido.

Cubren tres cosas que no se ven desde fuera pero que deciden si el registro de
informes sigue siendo fiable con el tiempo: dónde se apunta el fichero, qué
pasa si dos generaciones del mismo caso coinciden, y si el orden de la
cronología es realmente el que el informe declara.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.reports import repository, service
from app.modules.reports.models import Report
from app.modules.shared.models import TimelineEvent
from tests.conftest import NARRATIVA_FALSA


def _generar(db_session, case_id, generado_por="Tester"):
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa",
        return_value=NARRATIVA_FALSA,
    ):
        return service.generate_report(db_session, case_id=case_id, generado_por=generado_por)


# --- Dónde se apunta el fichero ---------------------------------------------


def test_archivo_pdf_se_guarda_como_ruta_relativa(db_session, case_con_timeline, storage_dir):
    """
    Guardarla absoluta ataba la fila a la máquina que generó el informe: al
    desplegar en Docker o mover el almacén, todas las filas anteriores
    apuntarían a ficheros que no existen.
    """
    report = _generar(db_session, case_con_timeline.id)

    assert report.archivo_pdf == f"case_{case_con_timeline.id}/report_v1.pdf"
    assert not Path(report.archivo_pdf).is_absolute()
    assert str(storage_dir) not in report.archivo_pdf


def test_la_ruta_relativa_se_resuelve_contra_el_almacen(db_session, case_con_timeline, storage_dir):
    report = _generar(db_session, case_con_timeline.id)

    _, ruta = service.get_report_file(db_session, report.id)

    assert ruta.is_file()
    assert ruta == storage_dir / f"case_{case_con_timeline.id}" / "report_v1.pdf"


def test_un_informe_antiguo_con_ruta_absoluta_se_sigue_sirviendo(
    db_session, case_con_timeline, storage_dir
):
    """
    Los informes emitidos antes de este cambio tienen la ruta absoluta en base
    de datos. Siguen siendo válidos mientras el fichero esté donde decía: no se
    migran, porque reescribir la ruta de un informe ya emitido es tocar el
    registro de algo que ya se firmó.
    """
    report = _generar(db_session, case_con_timeline.id)
    absoluta = storage_dir / f"case_{case_con_timeline.id}" / "report_v1.pdf"
    report.archivo_pdf = str(absoluta)
    db_session.commit()

    _, ruta = service.get_report_file(db_session, report.id)

    assert ruta == absoluta
    assert ruta.is_file()


# --- Colisión de versión -----------------------------------------------------


def test_la_base_de_datos_rechaza_dos_veces_la_misma_version(
    db_session, case_con_timeline, storage_dir
):
    """Sin esta restricción, dos «v2» distintos podrían convivir."""
    _generar(db_session, case_con_timeline.id)

    db_session.add(
        Report(
            case_id=case_con_timeline.id,
            resumen_ia="duplicado",
            archivo_pdf="case_1/report_v1.pdf",
            generado_por="Otro",
            version=1,
            fecha_generacion=datetime.now(timezone.utc),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_si_otra_generacion_se_adelanta_se_reintenta_con_la_siguiente_version(
    db_session, case_con_timeline, storage_dir
):
    """
    Se simula la carrera haciendo que el cálculo de versión devuelva una que ya
    está emitida. El informe no debe fallar: debe recomponerse con la
    siguiente, porque el número va impreso en el propio documento.
    """
    _generar(db_session, case_con_timeline.id)  # ocupa la v1
    real = repository.next_version

    with patch(
        "app.modules.reports.repository.next_version",
        side_effect=[1, real(db_session, case_con_timeline.id)],
    ):
        segundo = _generar(db_session, case_con_timeline.id)

    assert segundo.version == 2
    assert segundo.archivo_pdf.endswith("report_v2.pdf")
    assert (storage_dir / f"case_{case_con_timeline.id}" / "report_v2.pdf").is_file()


def test_si_la_colision_no_se_resuelve_no_se_emite_nada(
    db_session, case_con_timeline, storage_dir
):
    _generar(db_session, case_con_timeline.id)

    with patch("app.modules.reports.repository.next_version", return_value=1):
        with pytest.raises(service.VersionConflictError):
            _generar(db_session, case_con_timeline.id)

    # Ni fila nueva ni ficheros de una versión que nunca llegó a emitirse.
    assert len(repository.list_reports_for_case(db_session, case_con_timeline.id)) == 1
    assert not (storage_dir / f"case_{case_con_timeline.id}" / "report_v2.pdf").exists()


def test_la_colision_de_version_se_traduce_en_409(client, case_con_timeline, storage_dir):
    """No es culpa de la petición: reintentarla funciona, y 409 lo dice."""
    with patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        )

        with patch("app.modules.reports.repository.next_version", return_value=1):
            respuesta = client.post(
                "/reports/generate",
                json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
            )

    assert respuesta.status_code == 409


# --- Orden de la cronología --------------------------------------------------


def test_la_cronologia_desempata_por_fecha_y_por_id(db_session, case_con_timeline):
    """
    El apartado de metodología afirma que el orden es determinista. `orden` lo
    fija el Módulo 4 y no es único, así que sin desempate el orden entre
    empatados lo decidiría la base de datos.
    """
    base = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    for minutos in (30, 10, 20):
        db_session.add(
            TimelineEvent(
                id=f"tl-empate-{minutos}",
                case_id=case_con_timeline.id,
                fecha_hora=base + timedelta(minutes=minutos),
                descripcion=f"Empate a los {minutos} minutos",
                origen_modulo="tracking",
                origen_id=99,
                orden=0,  # mismo `orden` que el primer evento de la fixture
            )
        )
    db_session.commit()

    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    empatados = [e for e in eventos if e.orden == 0]

    assert [e.fecha_hora for e in empatados] == sorted(e.fecha_hora for e in empatados)
