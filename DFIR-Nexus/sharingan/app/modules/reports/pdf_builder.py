"""
Renderizado del informe a PDF (reportlab).

El contenido del informe —qué secciones tiene y qué dicen— vive en
`document.py`. Aquí solo se traduce cada bloque a los `Flowable` de reportlab.

Dos detalles de reportlab que importan y que son la razón de que este módulo
tenga tests propios:

* Todo texto que venga de la base de datos o del LLM se envuelve en
  `Paragraph` y se escapa con `xml.sax.saxutils.escape`. Una cadena suelta
  en una celda de `Table` NO hace salto de línea (se desborda de la
  columna), y reportlab interpreta mini-HTML, así que un `<` o un `&` en
  una descripción rompería la generación.
* El pie con "Página X de Y" necesita dos pasadas: el total no se conoce
  hasta terminar de componer, así que se guardan los estados de página y se
  pintan todos al final.
"""
import io
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.reports.document import (
    Documento,
    Espacio,
    Parrafo,
    SaltoPagina,
    Tabla,
    Titulo,
)

_styles = getSampleStyleSheet()
_CUERPO = ParagraphStyle(
    "CuerpoNexus",
    parent=_styles["Normal"],
    alignment=TA_JUSTIFY,
    spaceAfter=6,
    # Por defecto reportlab permite viudas: la última línea de un párrafo
    # puede quedarse sola al principio de la página siguiente. En un informe
    # que se lee en papel eso hace perder el hilo, y cerrarlo no cuesta nada.
    # (`allowOrphans` ya es 0 por defecto, o sea que la primera línea suelta
    # al pie de una página tampoco pasa.)
    allowWidows=0,
)
_CELDA = ParagraphStyle("CeldaNexus", parent=_styles["Normal"], fontSize=8, leading=10)
_CELDA_CABECERA = ParagraphStyle(
    "CeldaCabeceraNexus", parent=_CELDA, textColor=colors.white, fontName="Helvetica-Bold"
)

#: Un estilo de título por nivel, copiado del de la hoja de estilos de
#: reportlab con **`keepWithNext` activado**, que es lo que impide que un título
#: se quede solo al final de una página y su texto empiece en la siguiente.
#: Reportlab no lo pone: los `Heading` de `getSampleStyleSheet` no traen el
#: atributo, así que no sabe que un título va pegado a lo que anuncia y parte
#: donde le toca.
#:
#: Se copian en vez de tocar la hoja de estilos original porque
#: `getSampleStyleSheet` devuelve un objeto nuevo pero con estilos compartidos
#: por proceso: mutarlos afectaría a cualquier otro documento del mismo
#: servidor.
_ESTILO_TITULO = {
    nivel: ParagraphStyle(f"Titulo{nivel}Nexus", parent=_styles[nombre], keepWithNext=1)
    for nivel, nombre in ((0, "Title"), (1, "Heading1"), (2, "Heading2"))
}


def _p(texto: str, estilo: ParagraphStyle = _CUERPO) -> Paragraph:
    """Párrafo con el texto escapado: nunca pasar cadenas crudas a reportlab."""
    return Paragraph(escape(str(texto)), estilo)


#: Puntos por los que se puede partir un valor sin que deje de leerse: son los
#: separadores propios de dominios, URLs, correos, rutas y hashes con guiones.
_SEPARADORES = ".-/@_:?&=,;"

#: `LEFTPADDING` + `RIGHTPADDING` de `_tabla`. El texto no dispone del ancho
#: completo de la columna.
_RELLENO_CELDA = 8


def _celda(texto: str, ancho_pt: float | None) -> Paragraph:
    """
    Celda con los cortes de línea puestos donde el valor los admite.

    Cuando una palabra no cabe en la columna, reportlab la parte por donde le
    toca: `victima@dominio-c` / `orporativo.example.com`. Aquí se eligen antes,
    en los separadores del propio valor, que es como se parten las URLs en
    cualquier texto impreso: `…victima@` / `dominio-corporativo.example.` /
    `com`.

    La diferencia no es de exactitud —reportlab no inserta guion al partir, así
    que concatenar las líneas devuelve el valor íntegro en los dos casos, y hay
    un test que lo fija—, es de lectura. El Anexo B existe para que alguien
    pueda comprobar un indicador por su cuenta, casi siempre tecleándolo desde
    el papel, y un dominio troceado por la mitad de una etiqueta se comprueba
    mucho peor que uno troceado por sus puntos.

    Lo que no tiene separadores (un SHA-256) se deja como está: contra eso no
    hay nada mejor que el corte duro de reportlab.
    """
    if ancho_pt is None:
        return _p(texto, _CELDA)

    disponible = ancho_pt - _RELLENO_CELDA
    trozos = [
        escape(t) for t in _partir_por_separadores(str(texto), disponible)
    ]
    return Paragraph("<br/>".join(trozos), _CELDA)


def _partir_por_separadores(texto: str, disponible: float) -> list[str]:
    """
    Reparte `texto` en las líneas que caben, cortando solo donde haga falta.

    Solo se tocan las **palabras que por sí solas no caben** en la columna:
    todo lo demás se deja intacto para que lo reparta reportlab por los
    espacios, que es donde mejor queda. Saltarse esto rompía las celdas que ya
    se partían bien: `2026-08-03 13:00` acababa como `2026-08-03 13:` / `00`,
    con la hora cortada por el medio, cuando el espacio de en medio era un
    sitio perfectamente bueno para el salto.
    """
    if disponible <= 0 or _ancho(texto) <= disponible:
        return [texto]

    lineas = [""]
    for parte in re.split(r"(\s+)", texto):
        if parte.strip() and _ancho(parte) > disponible:
            trozos = _romper_palabra(parte, disponible)
            lineas[-1] += trozos[0]
            lineas.extend(trozos[1:])
        else:
            lineas[-1] += parte
    return lineas


def _romper_palabra(palabra: str, disponible: float) -> list[str]:
    """
    Trocea una palabra demasiado larga por sus separadores, de forma voraz.

    Devuelve la palabra entera si no hay por dónde partirla —un SHA-256— o si
    ni siquiera troceada gana nada: trocear sin necesidad también estropea la
    lectura, y para eso ya está el corte duro de reportlab.
    """
    lineas: list[str] = []
    actual = ""
    for segmento in _segmentos(palabra):
        if actual and _ancho(actual + segmento) > disponible:
            lineas.append(actual)
            actual = segmento
        else:
            actual += segmento
    if actual:
        lineas.append(actual)

    return lineas if len(lineas) > 1 else [palabra]


def _segmentos(texto: str) -> list[str]:
    """
    Trocea por separadores dejándolos al **final** de su segmento.

    Es lo que hace legible el corte: la línea termina en el punto o el guion,
    igual que en una URL partida a mano, en vez de empezar por él.
    """
    segmentos: list[str] = []
    actual = ""
    for caracter in texto:
        actual += caracter
        if caracter in _SEPARADORES:
            segmentos.append(actual)
            actual = ""
    if actual:
        segmentos.append(actual)
    return segmentos


def _ancho(texto: str) -> float:
    return stringWidth(texto, _CELDA.fontName, _CELDA.fontSize)


def _tabla(bloque: Tabla) -> Table:
    anchos = [ancho * cm for ancho in bloque.anchos_cm] if bloque.anchos_cm else None
    anchos_celda = anchos or [None] * len(bloque.cabeceras)

    datos = [[Paragraph(escape(c), _CELDA_CABECERA) for c in bloque.cabeceras]]
    datos += [
        [_celda(celda, ancho) for celda, ancho in zip(fila, anchos_celda)]
        for fila in bloque.filas
    ]

    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20242F")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabla


#: Identificación del equipo que firma el informe, impresa en el pie de todas
#: las páginas del PDF.
#:
#: Es un distintivo de autoría, equivalente a un membrete, y **vive en el pie
#: por decisión del grupo**. Antes se dibujaba centrada y en diagonal sobre la
#: hoja, muy tenue: aun al 7 % de opacidad competía con el texto, porque a
#: tamaño de titular manda la superficie de tinta y no el alfa. Y en un
#: documento pericial una marca legible de un vistazo se confunde con un sello
#: de estado —«BORRADOR», «COPIA»— y cambiaría lo que el documento dice de sí
#: mismo. En el pie identifica igual, no tapa nada y por eso ya no necesita
#: transparencia. El estado de la emisión lo declaran la portada y el
#: apartado 1.
MARCA_AGUA_GRUPO = "Expediente XSS"
MARCA_AGUA_LEMA = (
    "La verdad está ahí afuera, y también en tu input. "
    "XSS puede estar en cualquier lugar"
)

#: Altura de las dos líneas del pie, desde el borde inferior de la hoja. Las
#: dos van **por debajo del `bottomMargin`** de `construir_pdf` (2,2 cm), que
#: es lo que garantiza que el pie no se solape nunca con el contenido
#: compuesto; hay un test que lo comprueba sobre el PDF renderizado.
#:
#: Dos líneas y no una: el lema son 85 caracteres y, compartiendo línea con el
#: código y el «Página X de Y», dejaba menos de medio centímetro a cada lado.
_PIE_DATOS_Y = 1.55 * cm
_PIE_MARCA_Y = 1.0 * cm
_PIE_CUERPO = 7


class _CanvasNumerado(canvas.Canvas):
    """
    Pie de todas las páginas: código, «Página X de Y» y la marca del grupo.

    El total de páginas no se conoce hasta terminar de componer, así que se
    guardan los estados de página y se pintan todos al final (receta estándar
    de reportlab). Sin paginación una copia impresa no es auditable: no se
    detecta si falta una hoja.
    """

    codigo_informe = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas: list[dict] = []

    def showPage(self) -> None:  # noqa: N802 (API de reportlab)
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._dibujar_pie(total)
            super().showPage()
        super().save()

    def _dibujar_pie(self, total: int) -> None:
        self.saveState()
        self.setFont("Helvetica", _PIE_CUERPO)
        self.setFillColor(colors.grey)
        self.drawString(2 * cm, _PIE_DATOS_Y, self.codigo_informe)
        self.drawRightString(
            A4[0] - 2 * cm, _PIE_DATOS_Y, f"Página {self._pageNumber} de {total}"
        )
        self._dibujar_marca()
        self.restoreState()

    def _dibujar_marca(self) -> None:
        """
        Nombre del grupo en negrita y lema detrás, centrados en el pie.

        Se centra el conjunto y no cada parte por separado, así que hay que
        medir antes: `drawCentredString` centraría el nombre y el lema uno
        sobre otro en vez de uno detrás del otro.
        """
        nombre = f"{MARCA_AGUA_GRUPO}  ·  "
        ancho_nombre = stringWidth(nombre, "Helvetica-Bold", _PIE_CUERPO)
        ancho_total = ancho_nombre + stringWidth(
            MARCA_AGUA_LEMA, "Helvetica", _PIE_CUERPO
        )
        izquierda = (A4[0] - ancho_total) / 2
        self.setFont("Helvetica-Bold", _PIE_CUERPO)
        self.drawString(izquierda, _PIE_MARCA_Y, nombre)
        self.setFont("Helvetica", _PIE_CUERPO)
        self.drawString(izquierda + ancho_nombre, _PIE_MARCA_Y, MARCA_AGUA_LEMA)


def construir_pdf(documento: Documento) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=documento.titulo,
        author=documento.generado_por,
        subject=f"Informe pericial del caso {documento.case_id}",
        creator="DFIR Nexus — Módulo 5 (Sharingan)",
    )

    story: list = []
    for bloque in documento.bloques:
        match bloque:
            case Titulo(texto=texto, nivel=nivel):
                # Las secciones respiran; el título del documento y el de los
                # anexos ya traen su propio espaciado de la hoja de estilos.
                if nivel == 2:
                    story.append(Spacer(1, 0.5 * cm))
                story.append(Paragraph(escape(texto), _ESTILO_TITULO[nivel]))
            case Parrafo(texto=texto):
                story.append(_p(texto))
            case Tabla():
                story.append(_tabla(bloque))
            case Espacio(alto_cm=alto):
                story.append(Spacer(1, alto * cm))
            case SaltoPagina():
                story.append(PageBreak())

    lienzo = type(
        "_CanvasInforme", (_CanvasNumerado,), {"codigo_informe": documento.codigo}
    )
    doc.build(story, canvasmaker=lienzo)
    return buffer.getvalue()
