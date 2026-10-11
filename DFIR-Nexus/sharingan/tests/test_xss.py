"""
Tests de inyección en los formatos de salida.

El informe reproduce texto de los Módulos 1 a 4: nombres de dominio de OSINT,
líneas de log, descripciones de evidencia. Nada de eso lo escribe el Módulo 5,
y parte de ello lo elige el investigado —quien registra un dominio decide cómo
se llama—, así que se trata como contenido hostil.

La defensa principal es el escapado. La segunda es la política de contenido del
documento, que existe precisamente para el día en que la primera falle.
"""
import json
from html.parser import HTMLParser
from unittest.mock import patch

from app.modules.reports import repository
from app.modules.reports.docx_builder import construir_docx
from app.modules.reports.html_builder import CSP_INFORME, construir_html
from app.modules.reports.json_builder import construir_json
from app.modules.reports.pdf_builder import construir_pdf
from tests.conftest import NARRATIVA_FALSA, documento_de_prueba

#: Cargas pensadas cada una para un contexto distinto: etiqueta, ruptura de
#: atributo, manejador de evento, protocolo javascript y cierre del <style>.
CARGAS = [
    '<script>alert(1)</script>',
    '"><script>alert(2)</script>',
    "' onmouseover='alert(3)",
    '<img src=x onerror=alert(4)>',
    '<a href="javascript:alert(5)">pincha</a>',
    '</style><script>alert(6)</script>',
    '<svg/onload=alert(7)>',
]


def _caso_envenenado(db_session, caso, carga):
    """Mete la carga por todos los sitios por los que entra texto ajeno."""
    eventos = repository.get_timeline_events(db_session, caso.id)
    eventos[0].descripcion = carga
    eventos[0].origen_modulo = carga
    caso.nombre = carga
    caso.descripcion = carga
    caso.responsable = carga
    return documento_de_prueba(
        db_session, caso, eventos, generado_por=carga, notas=carga
    )


class _Inventario(HTMLParser):
    """Recoge qué etiquetas y atributos existen de verdad en el documento."""

    def __init__(self):
        super().__init__()
        self.etiquetas: set[str] = set()
        self.atributos: set[str] = set()

    def handle_starttag(self, tag, attrs):
        self.etiquetas.add(tag)
        self.atributos.update(nombre.lower() for nombre, _ in attrs)


def _inventario(html: str) -> _Inventario:
    parser = _Inventario()
    parser.feed(html)
    return parser


#: Lo único que el informe necesita. Cualquier otra cosa es una etiqueta que
#: alguien ha conseguido inyectar.
_ETIQUETAS_PERMITIDAS = {
    "html", "head", "meta", "title", "style", "body", "h1", "h2", "h3", "p",
    "div", "table", "thead", "tbody", "tr", "th", "td", "footer", "span",
}
_ATRIBUTOS_PERMITIDOS = {"lang", "charset", "http-equiv", "content", "name", "style", "class", "scope"}


def test_ninguna_carga_llega_a_crear_etiquetas_ni_atributos(db_session, case_con_anexos):
    """
    No se comprueba por subcadenas —eso confunde el texto escapado con el
    marcado real— sino parseando el HTML: lo que importa es qué etiquetas y
    qué atributos existen de verdad después de meter la carga.
    """
    for carga in CARGAS:
        html = construir_html(_caso_envenenado(db_session, case_con_anexos, carga)).decode()
        inventario = _inventario(html)

        intrusas = inventario.etiquetas - _ETIQUETAS_PERMITIDAS
        assert not intrusas, f"la carga {carga!r} creó las etiquetas {intrusas}"

        colados = inventario.atributos - _ATRIBUTOS_PERMITIDOS
        assert not colados, f"la carga {carga!r} creó los atributos {colados}"
        assert not any(a.startswith("on") for a in inventario.atributos)


def test_la_carga_nunca_aparece_literal_en_el_documento(db_session, case_con_anexos):
    """Si aparece tal cual, es que no ha pasado por el escapado."""
    for carga in CARGAS:
        html = construir_html(_caso_envenenado(db_session, case_con_anexos, carga)).decode()

        assert carga not in html, f"la carga {carga!r} salió sin escapar"


def test_el_html_escapa_tambien_las_comillas(db_session, case_con_timeline):
    """
    `html.escape` escapa comillas por defecto, pero es la diferencia entre que
    una carga se salga de un atributo o no. Si alguien lo cambiara a
    `quote=False` por «limpiar» la salida, este test lo cazaría.
    """
    doc = _caso_envenenado(db_session, case_con_timeline, '" onmouseover="alert(1)')
    html = construir_html(doc).decode()

    cuerpo = html.split("</head>", 1)[1]
    assert "&quot;" in cuerpo
    assert ' onmouseover="alert(1)"' not in cuerpo


def test_el_html_declara_una_politica_de_contenido(db_session, case_con_timeline):
    """
    Es la red de seguridad: si un día se escapase mal, el navegador seguiría
    sin ejecutar nada. Va incrustada en el documento porque el informe se
    archiva y se abre desde disco, donde no hay cabeceras HTTP.
    """
    html = construir_html(documento_de_prueba(db_session, case_con_timeline)).decode()

    assert 'http-equiv="Content-Security-Policy"' in html
    assert "default-src 'none'" in CSP_INFORME
    assert "script-src" not in CSP_INFORME  # nada de scripts: ni propios


def test_el_html_no_carga_nada_de_fuera(db_session, case_con_anexos):
    """Un documento archivado no debe depender de que un tercero siga vivo."""
    html = construir_html(documento_de_prueba(db_session, case_con_anexos)).decode()

    for señal in ("<script", "<iframe", "<object", "<embed", "src=", "http://", "https://"):
        assert señal not in html, f"el informe carga algo externo: {señal}"


def test_los_otros_tres_formatos_tampoco_se_rompen(db_session, case_con_anexos):
    """
    El PDF y el DOCX no ejecutan scripts, pero sí se rompen si el texto se
    inserta crudo en su marcado interno; el JSON tiene que escapar para no
    dejar de ser JSON válido.
    """
    for carga in CARGAS:
        doc = _caso_envenenado(db_session, case_con_anexos, carga)

        assert construir_pdf(doc).startswith(b"%PDF")
        assert construir_docx(doc).startswith(b"PK")  # un .docx es un zip
        contenido = json.loads(construir_json(doc))  # revienta si no es válido
        assert contenido["informe"]["generado_por"] == carga


def test_la_descarga_del_html_llega_con_su_politica_y_sin_adivinar_el_tipo(
    client, case_con_timeline, storage_dir
):
    with patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        report = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        ).json()

    respuesta = client.get(f"/reports/{report['id']}/download?formato=html")

    assert respuesta.headers["content-security-policy"] == CSP_INFORME
    assert respuesta.headers["x-content-type-options"] == "nosniff"


def test_ninguna_respuesta_permite_adivinar_el_tipo(client, case_con_timeline, storage_dir):
    """
    Sin `nosniff`, un navegador puede decidir que una respuesta JSON «parece»
    HTML y renderizarla, con el texto de los otros módulos dentro.
    """
    with patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        report = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        ).json()

    for ruta in (f"/reports/{report['id']}", f"/reports/{report['id']}/download?formato=json", "/health"):
        respuesta = client.get(ruta)
        assert respuesta.headers["x-content-type-options"] == "nosniff", ruta
