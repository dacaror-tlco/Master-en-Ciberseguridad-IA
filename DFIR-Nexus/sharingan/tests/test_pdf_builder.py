"""
Tests del generador de PDF. Comprueban las trampas concretas de reportlab
(desbordamiento de celdas, mini-HTML) y que el documento lleva lo que un
informe pericial tiene que llevar.
"""
import io
from collections import defaultdict
from datetime import datetime

from pypdf import PdfReader
from reportlab.lib.units import cm

from app.modules.reports import repository
from app.modules.reports.document import Documento, Parrafo, Titulo
from app.modules.reports.pdf_builder import construir_pdf
from tests.conftest import NARRATIVA_FALSA, documento_de_prueba

#: `bottomMargin` de `construir_pdf`: por encima de esta altura está la caja de
#: contenido, por debajo solo puede haber pie.
_MARGEN_INFERIOR = 2.2 * cm


def _construir(db_session, caso, eventos=None, **extra):
    return construir_pdf(documento_de_prueba(db_session, caso, eventos, **extra))


def _texto(pdf_bytes: bytes) -> str:
    lector = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(pagina.extract_text() or "" for pagina in lector.pages)


def _lineas_por_pagina(pdf_bytes: bytes) -> list[list[tuple[str, float]]]:
    """
    Cada página como lista de `(texto, altura)`, con la altura en puntos desde
    el borde inferior de la hoja.

    `extract_text` a secas devuelve el texto plano y no dice dónde está, así que
    para los tests de maquetación hace falta el visitante de pypdf, que va
    dando cada fragmento con dos matrices.

    **La altura es `tm[5] + cm[5]`, no `tm[5]`.** Platypus compone cada
    `Flowable` en su propio sistema de coordenadas: traslada el lienzo hasta la
    posición del bloque (eso queda en `cm`) y dentro escribe con `tm` casi a
    cero. Con solo `tm[5]` todo el contenido del informe aparece a 2 o 4 pt del
    borde inferior, o sea por debajo del pie, y cualquier comprobación de
    posición sale vacía y pasa siempre. El pie sí es la excepción: se dibuja
    directo sobre el lienzo y ahí `cm[5]` vale 0.

    Los fragmentos de una misma línea llegan por separado —reportlab parte un
    párrafo justificado en varios— y se reagrupan por altura.
    """
    paginas = []
    for pagina in PdfReader(io.BytesIO(pdf_bytes)).pages:
        fragmentos: dict[float, list[str]] = defaultdict(list)

        def visitar(texto, cm_actual, tm, _fuente, _tam, destino=fragmentos):
            if texto.strip():
                destino[round(tm[5] + cm_actual[5], 1)].append(texto)

        pagina.extract_text(visitor_text=visitar)
        paginas.append(
            [("".join(partes).strip(), altura) for altura, partes in fragmentos.items()]
        )
    return paginas


def test_pdf_tiene_las_secciones_periciales(db_session, case_con_anexos):
    texto = _texto(_construir(db_session, case_con_anexos))

    for seccion in (
        "Objeto y alcance",
        "Antecedentes",
        "Material analizado",
        "Metodología",
        "Cronología de eventos",
        "Hallazgos",
        "Conclusiones",
        "inteligencia artificial",
        "Firma",
        "Anexo A",
        "Anexo B",
        "Anexo C",
    ):
        assert seccion in texto, f"falta la sección «{seccion}»"


def test_pdf_declara_codigo_version_y_paginacion(db_session, case_con_anexos):
    texto = _texto(_construir(db_session, case_con_anexos))

    assert f"INF-{case_con_anexos.id:04d}-v1" in texto
    assert "Página 1 de" in texto


def test_pdf_declara_el_modelo_de_ia_usado(db_session, case_con_anexos):
    texto = _texto(_construir(db_session, case_con_anexos))

    assert NARRATIVA_FALSA.modelo in texto
    assert NARRATIVA_FALSA.version_prompt in texto


def test_descripcion_larga_se_reparte_en_varias_lineas(db_session, case_con_timeline):
    """
    Una cadena suelta en una celda de Table no envuelve y se sale de la
    columna. Con Paragraph, un texto largo ocupa varias líneas y el
    documento crece: eso es lo que comprobamos.
    """
    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    corto = _construir(db_session, case_con_timeline, eventos=list(eventos))

    eventos[0].descripcion = "palabra " * 200
    largo = _construir(db_session, case_con_timeline, eventos=eventos)

    assert len(largo) > len(corto)
    assert "palabra palabra" in _texto(largo)


def test_caracteres_xml_no_rompen_el_pdf(db_session, case_con_timeline):
    """reportlab interpreta mini-HTML: un `<` o un `&` sin escapar lo revienta."""
    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)
    eventos[0].descripcion = 'Payload <script>alert("x")</script> & "comillas"'
    case_con_timeline.descripcion = "Cliente <Acme> & filial"

    pdf = _construir(
        db_session, case_con_timeline, eventos=eventos, generado_por="Ana <Pérez> & Cía"
    )

    assert pdf.startswith(b"%PDF")
    assert "<script>" in _texto(pdf)


def test_notas_del_perito_aparecen_en_antecedentes(db_session, case_con_anexos):
    texto = _texto(
        _construir(db_session, case_con_anexos, notas="Priorizar el vector de entrada.")
    )

    assert "Instrucciones recibidas" in texto
    assert "Priorizar el vector de entrada." in texto


def test_cronologia_referencia_el_registro_de_origen(db_session, case_con_timeline):
    """Sin la referencia módulo#id, el informe es narrativa sin trazabilidad."""
    texto = _texto(_construir(db_session, case_con_timeline))

    assert "tracking#0" in texto
    assert "Ref." in texto


# --- Cortes de línea dentro de las celdas ------------------------------------
#
# Los valores del Anexo B (dominios, URLs, correos) no caben en su columna y
# reportlab los parte por donde le toca, por la mitad de una etiqueta. El
# anexo existe para que alguien compruebe un indicador por su cuenta, casi
# siempre tecleándolo desde el papel, así que dónde cae el corte importa.

from reportlab.lib.units import cm  # noqa: E402

from app.modules.reports.pdf_builder import (  # noqa: E402
    _RELLENO_CELDA,
    _partir_por_separadores,
)

ANCHO_INDICADOR = 4.1 * cm - _RELLENO_CELDA  # la columna «Indicador» del Anexo B


def test_un_valor_largo_se_parte_por_sus_separadores():
    lineas = _partir_por_separadores(
        "correo-de-la-victima@dominio-corporativo.example.com", ANCHO_INDICADOR
    )

    assert len(lineas) > 1
    # Cada línea salvo la última termina en un separador del propio valor,
    # que es lo que hace el corte legible.
    assert all(linea[-1] in ".-/@_:?&=,;" for linea in lineas[:-1])


def test_partir_nunca_cambia_el_valor():
    """
    La propiedad que de verdad hay que sostener: el corte no añade ni quita un
    solo carácter. Un indicador de un informe pericial que no se pueda
    reconstruir juntando sus líneas no vale para nada.
    """
    valores = [
        "correo-de-la-victima@dominio-corporativo.example.com",
        "https://cdn.entrega-documentos.example.net/factura/2026/08/adjunto.zip",
        "3b1f0a9c8e7d6b5a4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b",
        "203.0.113.10",
        "Emiratos Árabes Unidos",
    ]
    for valor in valores:
        assert "".join(_partir_por_separadores(valor, ANCHO_INDICADOR)) == valor


def test_lo_que_cabe_o_no_tiene_por_donde_partirse_se_deja_en_una_linea():
    """
    Trocear sin necesidad también estropea la lectura. Un SHA-256 no tiene
    separadores: no se gana nada partiéndolo por un sitio cualquiera, así que
    se deja entero y decide reportlab.
    """
    assert _partir_por_separadores("203.0.113.10", ANCHO_INDICADOR) == ["203.0.113.10"]
    assert _partir_por_separadores("a" * 80, ANCHO_INDICADOR) == ["a" * 80]


def test_el_texto_normal_no_se_toca():
    """Las descripciones y los nombres se parten por espacios, como siempre."""
    frase = "Se detecta acceso no autorizado al servidor"
    assert _partir_por_separadores(frase, ANCHO_INDICADOR) == [frase]


def test_no_se_parte_lo_que_ya_tenia_donde_partirse():
    """
    Regresión: la columna «Consulta (UTC)» del Anexo B mide 2,3 cm y su
    contenido no cabe entero, pero tiene un espacio en medio. Partir por
    separadores sin mirar los espacios dejaba `2026-08-03 13:` / `00`, con la
    hora cortada por la mitad, habiendo un sitio mucho mejor para el salto.
    """
    ancho_consulta = 2.3 * cm - _RELLENO_CELDA
    assert _partir_por_separadores("2026-08-03 13:00", ancho_consulta) == ["2026-08-03 13:00"]


def test_solo_se_toca_la_palabra_que_no_cabe():
    """En una frase con una URL larga, la frase sigue entera; la URL no."""
    frase = "Se accede a https://muy-largo.example.com/ruta/profunda y se descarga"
    lineas = _partir_por_separadores(frase, ANCHO_INDICADOR)

    assert "".join(lineas) == frase
    assert lineas[0].startswith("Se accede a https://")
    assert lineas[-1].endswith(" y se descarga")


def test_la_marca_de_agua_del_grupo_esta_en_todas_las_paginas(db_session, case_con_anexos):
    """
    La marca identifica al equipo que firma, así que no puede aparecer solo en
    la portada: una hoja suelta del informe tiene que poder atribuirse.
    """
    from app.modules.reports.pdf_builder import MARCA_AGUA_GRUPO, MARCA_AGUA_LEMA

    lector = PdfReader(io.BytesIO(_construir(db_session, case_con_anexos)))
    assert len(lector.pages) > 1, "el informe de prueba debe tener varias páginas"

    for numero, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        assert MARCA_AGUA_GRUPO in texto, f"falta el nombre del grupo en la página {numero}"
        assert MARCA_AGUA_LEMA in texto, f"falta el lema en la página {numero}"


def test_la_marca_del_grupo_vive_en_el_pie_y_no_sobre_el_texto(
    db_session, case_con_anexos
):
    """
    La marca va en el pie, por debajo del margen inferior de la caja de
    contenido. Ahí es donde no tapa nada, y es lo que la separa de un sello de
    estado: centrada sobre la hoja, una marca legible de un vistazo se confunde
    con un «BORRADOR» o un «COPIA» y cambia lo que el documento dice de sí
    mismo.

    Se comprueba sobre la coordenada del PDF renderizado y no sobre una
    constante, porque lo que importa es dónde acaba la tinta.
    """
    from app.modules.reports.pdf_builder import MARCA_AGUA_GRUPO

    pdf = _construir(db_session, case_con_anexos)
    for numero, lineas in enumerate(_lineas_por_pagina(pdf), start=1):
        marca = [y for texto, y in lineas if MARCA_AGUA_GRUPO in texto]
        assert marca, f"falta la marca en la página {numero}"
        assert max(marca) < _MARGEN_INFERIOR, (
            f"la marca de la página {numero} entra en la caja de contenido "
            f"(y={max(marca):.1f} pt, el contenido empieza en "
            f"{_MARGEN_INFERIOR:.1f} pt)"
        )


#: Relleno de una línea justa, para empujar un título hasta el borde inferior
#: de la página en `test_ningun_titulo_se_queda_solo_al_final_de_su_pagina`.
_RELLENO_UNA_LINEA = "Registro de relleno para empujar la maquetación."
_TITULO_VIGILADO = "Hallazgos"


def test_ningun_titulo_se_queda_solo_al_final_de_su_pagina():
    """
    Un título al pie de una página con su texto en la siguiente es la clase de
    detalle que en un informe pericial se lee como descuido. Reportlab no lo
    evita solo: hay que declarar `keepWithNext` en los estilos de título, y este
    test es lo que impide que alguien los sustituya por los de la hoja de
    estilos de reportlab, que no lo traen.

    **El caso límite se construye a propósito**, variando el relleno que
    precede al título hasta que cae justo en el borde de la página. Un solo
    documento de ejemplo no sirve: con el informe de prueba de los demás tests
    esta comprobación pasaba igual sin `keepWithNext`, porque ahí no había
    ningún título que cayera al final de una página. Un test que da lo mismo
    con el fallo puesto y quitado no comprueba nada.
    """
    for relleno in range(30, 46):
        documento = Documento(
            codigo="INF-9999-v1",
            case_id=9999,
            case_nombre="Maquetación",
            version=1,
            generado_por="tests",
            generado_el=datetime(2026, 9, 26, 12, 0),
            modelo_ia="ninguno",
            bloques=[
                *(Parrafo(_RELLENO_UNA_LINEA) for _ in range(relleno)),
                Titulo(_TITULO_VIGILADO, nivel=2),
                Parrafo(_RELLENO_UNA_LINEA),
            ],
        )

        for numero, lineas in enumerate(
            _lineas_por_pagina(construir_pdf(documento)), start=1
        ):
            contenido = [(texto, y) for texto, y in lineas if y >= _MARGEN_INFERIOR]
            if not contenido:
                continue
            ultima = min(contenido, key=lambda linea: linea[1])[0]
            assert ultima != _TITULO_VIGILADO, (
                f"con {relleno} párrafos de relleno, la página {numero} acaba "
                f"en el título «{_TITULO_VIGILADO}» y su texto empieza en la "
                f"siguiente"
            )
