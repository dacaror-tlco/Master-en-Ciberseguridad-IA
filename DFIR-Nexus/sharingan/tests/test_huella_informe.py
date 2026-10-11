"""
Huella SHA-256 del informe emitido.

Antes de esto, la única comprobación al descargar era que el fichero
existiese. Sustituirlo en disco por otro documento no lo detectaba nadie y la
API lo servía igual, presentándolo como el informe pericial emitido en su día.
Estos tests cubren las dos mitades: que la huella se registre sobre lo que de
verdad se emitió, y que un fichero que ya no coincide no llegue a servirse.
"""
import hashlib
from unittest.mock import patch

import pytest

from app.modules.reports import service
from app.modules.reports.formats import FormatoInforme
from tests.conftest import NARRATIVA_FALSA


def _generar(db_session, case_id):
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa",
        return_value=NARRATIVA_FALSA,
    ):
        return service.generate_report(db_session, case_id=case_id, generado_por="Tester")


def _ruta(report, formato):
    return service._ruta_absoluta(report.archivo_pdf, formato)


# --- Se registra lo que se emitió -------------------------------------------


def test_se_registra_una_huella_por_cada_formato_emitido(
    db_session, case_con_timeline, storage_dir
):
    """Las cuatro copias se emiten juntas; las cuatro deben quedar cubiertas."""
    report = _generar(db_session, case_con_timeline.id)

    assert set(report.huellas) == {formato.value for formato in FormatoInforme}


@pytest.mark.parametrize("formato", list(FormatoInforme))
def test_la_huella_es_la_del_fichero_realmente_escrito(
    db_session, case_con_timeline, storage_dir, formato
):
    """
    La huella se calcula sobre los bytes compuestos, no releyendo el disco.
    Este test es el que comprueba que ambos son lo mismo: si se guardase la
    huella de una cosa y en disco quedase otra, todas las descargas fallarían.
    """
    report = _generar(db_session, case_con_timeline.id)

    en_disco = hashlib.sha256(_ruta(report, formato).read_bytes()).hexdigest()

    assert report.huellas[formato.value] == en_disco
    assert len(en_disco) == 64


def test_dos_versiones_del_mismo_caso_tienen_huellas_distintas(
    db_session, case_con_timeline, storage_dir
):
    """El código de informe va impreso dentro: v1 y v2 no son el mismo fichero."""
    primero = _generar(db_session, case_con_timeline.id)
    huellas_v1 = dict(primero.huellas)
    segundo = _generar(db_session, case_con_timeline.id)

    assert segundo.version == 2
    assert segundo.huellas["pdf"] != huellas_v1["pdf"]


# --- No se sirve lo que ya no coincide --------------------------------------


def test_un_pdf_sustituido_en_disco_no_se_sirve(
    db_session, case_con_timeline, storage_dir
):
    report = _generar(db_session, case_con_timeline.id)
    _ruta(report, FormatoInforme.PDF).write_bytes(b"%PDF-1.4 otro documento cualquiera")

    with pytest.raises(service.ReportTamperedError):
        service.get_report_file(db_session, report.id, FormatoInforme.PDF)


def test_basta_con_alterar_un_byte(db_session, case_con_timeline, storage_dir):
    """
    Un informe manipulado no tiene por qué parecerlo: cambiar una cifra de una
    fecha o un nombre deja el documento del mismo tamaño y con el mismo
    aspecto. Es el caso que la comprobación de existencia nunca vio.
    """
    report = _generar(db_session, case_con_timeline.id)
    ruta = _ruta(report, FormatoInforme.HTML)
    contenido = bytearray(ruta.read_bytes())
    contenido[-1] = (contenido[-1] + 1) % 256
    ruta.write_bytes(bytes(contenido))

    with pytest.raises(service.ReportTamperedError):
        service.get_report_file(db_session, report.id, FormatoInforme.HTML)


def test_alterar_una_copia_no_bloquea_las_demas(
    db_session, case_con_timeline, storage_dir
):
    """
    Cada copia responde de sí misma. El PDF es el documento firmado: que
    alguien toque el DOCX no es motivo para dejar de servirlo.
    """
    report = _generar(db_session, case_con_timeline.id)
    _ruta(report, FormatoInforme.DOCX).write_bytes(b"no es un docx")

    _, ruta = service.get_report_file(db_session, report.id, FormatoInforme.PDF)
    assert ruta.is_file()

    with pytest.raises(service.ReportTamperedError):
        service.get_report_file(db_session, report.id, FormatoInforme.DOCX)


def test_la_manipulacion_se_traduce_en_409(client, case_con_timeline, storage_dir, db_session):
    """
    409 y no 410: el 410 significa «esta copia no se emitió nunca», que es
    normal en los informes antiguos. Quien descarga tiene que poder
    distinguirlo de un fichero que ya no es el que el informe declara.
    """
    report = _generar(db_session, case_con_timeline.id)
    _ruta(report, FormatoInforme.PDF).write_bytes(b"otro documento")

    respuesta = client.get(f"/reports/{report.id}/download")

    assert respuesta.status_code == 409
    assert "huella" in respuesta.json()["detail"]


# --- Compatibilidad y publicación -------------------------------------------


def test_un_informe_sin_huella_registrada_se_sigue_sirviendo(
    db_session, case_con_timeline, storage_dir
):
    """
    Los informes emitidos antes de esta columna no la tienen, y no se les
    calcula a posteriori: el hash del fichero que hoy hay en disco no
    demuestra que sea el que se emitió. Se sirven, sin verificar.
    """
    report = _generar(db_session, case_con_timeline.id)
    report.huellas = None
    db_session.commit()

    _, ruta = service.get_report_file(db_session, report.id, FormatoInforme.PDF)

    assert ruta.is_file()


def test_la_descarga_publica_la_huella_en_una_cabecera(
    client, case_con_timeline, storage_dir, db_session
):
    """
    Una huella que solo comprueba el servidor no demuestra nada a quien recibe
    el documento: tiene que poder contrastarlo por su cuenta.
    """
    report = _generar(db_session, case_con_timeline.id)

    respuesta = client.get(f"/reports/{report.id}/download")

    assert respuesta.status_code == 200
    assert respuesta.headers["X-Informe-SHA256"] == report.huellas["pdf"]
    assert hashlib.sha256(respuesta.content).hexdigest() == report.huellas["pdf"]


def test_la_api_devuelve_las_huellas_del_informe(
    client, case_con_timeline, storage_dir, db_session
):
    report = _generar(db_session, case_con_timeline.id)

    cuerpo = client.get(f"/reports/{report.id}").json()

    assert cuerpo["huellas"] == report.huellas
