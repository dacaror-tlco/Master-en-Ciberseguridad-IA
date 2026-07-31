"""
Generación del informe PDF combinado.

Junta los casos seleccionados de todos los módulos en un único documento
pensado para adjuntar a una denuncia. No sustituye el criterio de las
autoridades ni constituye por sí mismo una prueba pericial, pero organiza
toda la evidencia técnica recopilada de forma clara y con marca de tiempo
de cuándo se generó cada análisis.

Estructura del documento (por qué está diseñado así):

- **Portada + índice con marcadores PDF** (`_ReportDocTemplate.afterFlowable`
  + `TableOfContents`): un informe de evidencias con varias decenas de
  páginas sin forma de navegarlo no es utilizable como documento de apoyo
  para una denuncia — el índice enlaza a cada sección y cada caso.
- **`doc.multiBuild` + `_NumberedCanvas`**: el índice necesita saber en qué
  página cae cada sección ANTES de haber terminado de maquetar el
  documento entero, así que se construye en dos pasadas (estándar de
  reportlab). Aprovechamos esa segunda pasada para poder escribir
  "Página X de Y" en el pie — con una sola pasada no se conoce Y hasta el
  final.
- **Cada caso envuelto en `KeepTogether`** (ver `_append_section`): la
  versión anterior dejaba que reportlab partiera las tablas donde
  cayera el límite de página, lo que producía saltos como una tabla de
  señales cortada tras una sola fila, con la fila siguiente sola en la
  página siguiente. `KeepTogether` mueve el bloque completo de un caso a
  la página siguiente si no cabe entero en la que queda; si el caso en sí
  es más largo que una página completa, se permite que se divida con
  normalidad (comportamiento documentado de reportlab) — no hay forma de
  evitar eso sin cortar contenido, pero al menos empieza a partirse desde
  el principio de una página nueva, no a mitad de una casi llena.
- **La cabecera de cada sección va DENTRO del `KeepTogether` del primer
  caso**, no como párrafo suelto con `keepWithNext`: reportlab rechaza
  agrupar un `KeepTogether` dentro de otro `KeepTogether` automático (ver
  `_ktAllow` en su código fuente), así que `keepWithNext` no tiene efecto
  cuando el siguiente elemento ya es un bloque envuelto — la única forma
  fiable de que la cabecera de sección nunca quede huérfana al final de
  una página es incluirla en la lista de flowables del primer bloque.
"""
import hashlib
from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as _canvaslib
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from app.models.case import Case
from app.models.cnmv_check_case import CnmvCheckCase
from app.models.email_case import EmailCase
from app.models.facial_search_case import FacialSearchCase
from app.models.image_case import ImageCase
from app.models.ip_case import IpCase
from app.models.phone_case import PhoneCase
from app.models.reverse_image_search_case import ReverseImageSearchCase
from app.models.typosquatting_case import TyposquattingCase
from app.models.wallet_case import WalletCase

# ============================================================
# Paleta e identidad visual
#
# Los colores están emparentados con los del panel web (frontend/index.html:
# --accent, --risk-high/medium/low) pero NO son los mismos valores: la
# paleta del panel está pensada para texto sobre fondo OSCURO, y sobre un
# PDF de fondo blanco esos mismos tonos (pensados para contraste en modo
# oscuro) quedan lavados y con poco contraste — aquí se usan versiones más
# saturadas/oscuras de la misma familia de color, ajustadas para lectura e
# impresión en papel.
# ============================================================
_BRAND_COLOR = colors.HexColor("#1F2A44")        # azul marino — identidad principal del documento
_ACCENT_COLOR = colors.HexColor("#0E7D71")       # verde azulado — pariente del turquesa de acento del panel, oscurecido para fondo blanco
_SEVERITY_COLORS = {
    "high": colors.HexColor("#C0272D"),
    "medium": colors.HexColor("#B0680A"),
    "low": colors.HexColor("#1E8E5A"),
}
_SEVERITY_LABELS_ES = {"high": "ALTA", "medium": "MEDIA", "low": "BAJA"}
_ALERT_STYLES = {  # kind -> (fondo, color de acento)
    "info": (colors.HexColor("#EEF1F7"), _BRAND_COLOR),
    "warning": (colors.HexColor("#FFF6E9"), _SEVERITY_COLORS["medium"]),
    "danger": (colors.HexColor("#FDECEA"), _SEVERITY_COLORS["high"]),
}
_LINE_COLOR = colors.HexColor("#DDDDDD")
_MUTED_TEXT = colors.HexColor("#666666")
_ROW_ALT_COLOR = colors.HexColor("#F7F8FA")
_LABEL_BG = colors.HexColor("#F4F5F7")

_PAGE_MARGIN = 2 * cm
_CONTENT_WIDTH = A4[0] - 2 * _PAGE_MARGIN  # ancho útil real, para que todas las tablas alineen su borde derecho

_styles = getSampleStyleSheet()
_styles.add(ParagraphStyle("Kicker", parent=_styles["Normal"], fontName="Helvetica-Bold", fontSize=9.5, textColor=_ACCENT_COLOR, spaceAfter=6))
_styles.add(ParagraphStyle("ReportTitle", parent=_styles["Title"], textColor=_BRAND_COLOR, fontSize=21, leading=25, alignment=TA_LEFT, spaceAfter=6))
_styles.add(ParagraphStyle("CoverMeta", parent=_styles["Normal"], fontSize=9.5, textColor=_MUTED_TEXT, spaceAfter=2))
_styles.add(ParagraphStyle("TOCHeading", parent=_styles["Heading1"], textColor=_BRAND_COLOR, spaceAfter=14))
_styles.add(ParagraphStyle("SectionHeading", parent=_styles["Heading1"], textColor=_BRAND_COLOR, fontSize=15, spaceBefore=0, spaceAfter=10))
_styles.add(ParagraphStyle("SubHeading", parent=_styles["Heading2"], textColor=_BRAND_COLOR, fontSize=12, spaceBefore=8, spaceAfter=4))
_styles.add(ParagraphStyle("SmallGray", parent=_styles["Normal"], textColor=_MUTED_TEXT, fontSize=9))
_styles.add(ParagraphStyle("BodyText2", parent=_styles["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY))
_styles.add(ParagraphStyle("FieldLabel", parent=_styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, textColor=_BRAND_COLOR, spaceBefore=4, spaceAfter=5))
_styles.add(ParagraphStyle("CellText", parent=_styles["Normal"], fontSize=9.5, leading=13, alignment=TA_LEFT))
_styles.add(ParagraphStyle("CellTextBold", parent=_styles["CellText"], fontName="Helvetica-Bold"))
_styles.add(ParagraphStyle("CellTextWhite", parent=_styles["CellTextBold"], textColor=colors.white))
_styles.add(ParagraphStyle("StatLabel", parent=_styles["Normal"], fontSize=7.7, textColor=_MUTED_TEXT, fontName="Helvetica-Bold"))
_styles.add(ParagraphStyle("StatValue", parent=_styles["Normal"], fontSize=15, leading=18, spaceBefore=2, fontName="Helvetica-Bold"))
_styles.add(ParagraphStyle("AlertText", parent=_styles["Normal"], fontSize=9.5, leading=13, alignment=TA_LEFT))
_styles.add(ParagraphStyle("TOCLevel0", parent=_styles["Normal"], fontSize=11, leading=16, textColor=_BRAND_COLOR, fontName="Helvetica-Bold"))
_styles.add(ParagraphStyle("TOCLevel1", parent=_styles["Normal"], fontSize=9.5, leading=13, leftIndent=14, textColor=colors.HexColor("#444444")))


# ============================================================
# Bloques de construcción reutilizables
# ============================================================

def _score_color(score: int):
    if score >= 60:
        return _SEVERITY_COLORS["high"]
    if score >= 30:
        return _SEVERITY_COLORS["medium"]
    return _SEVERITY_COLORS["low"]


def _hr(color=_LINE_COLOR, thickness=0.6):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceBefore=2, spaceAfter=10)


def _field(label: str) -> Paragraph:
    """
    Etiqueta de subsección (WHOIS, Certificado SSL, Señales de riesgo...).
    Antes usaba el mismo estilo que un párrafo de cuerpo normal — sin
    ninguna jerarquía tipográfica real el documento se veía plano, una de
    las razones por las que "se notaba hecho por IA".
    """
    return Paragraph(_xml_escape(label), _styles["FieldLabel"])


def _block(*flowables) -> KeepTogether:
    """
    Agrupa una etiqueta de subsección con su contenido (tabla/párrafo) para
    que salte de página como unidad. Sin esto, un caso más largo que una
    página (que ya no cabe entero en el KeepTogether de `_append_section`,
    y por tanto cae de vuelta al reparto normal por líneas) puede partir
    una tabla pequeña justo por la mitad — se comprobó en la práctica:
    una tabla DNS de 4 filas se partió 2+2 entre dos páginas. Anidar
    KeepTogether SÍ está soportado por reportlab durante ese reparto
    normal (a diferencia de `keepWithNext`, que rechaza explícitamente
    agrupar un KeepTogether con lo que le sigue — ver docstring del
    módulo), así que cada subsección queda protegida igual que el caso
    completo.
    """
    return KeepTogether(list(flowables))


def _kv_table(pairs: list[tuple[str, str]], col_widths=None) -> Table:
    """Tabla de dos columnas (etiqueta / valor) para los datos técnicos de cada caso."""
    rows = [
        [Paragraph(_xml_escape(str(label)), _styles["CellTextBold"]),
         Paragraph(str(value) if value not in (None, "") else "—", _styles["CellText"])]
        for label, value in pairs
    ]
    widths = col_widths or [5.5 * cm, _CONTENT_WIDTH - 5.5 * cm]
    table = Table(rows, colWidths=widths)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE_COLOR),
        ("BACKGROUND", (0, 0), (0, -1), _LABEL_BG),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, _ROW_ALT_COLOR]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _severity_chip(severity: str) -> Table:
    color = _SEVERITY_COLORS.get(severity, colors.grey)
    label = _SEVERITY_LABELS_ES.get(severity, severity.upper())
    chip = Table([[Paragraph(label, _styles["CellTextWhite"])]], colWidths=[2 * cm])
    chip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return chip


def _flags_table(flags: list[dict]):
    if not flags:
        return Paragraph("No se detectaron señales de riesgo en este análisis.", _styles["SmallGray"])

    header = [Paragraph("Severidad", _styles["CellTextWhite"]), Paragraph("Señal", _styles["CellTextWhite"]), Paragraph("Descripción", _styles["CellTextWhite"])]
    rows = [header]
    for flag in flags:
        severity = flag.get("severity", "low")
        rows.append([
            _severity_chip(severity),
            Paragraph(flag.get("code", ""), _styles["CellTextBold"]),
            Paragraph(flag.get("description", ""), _styles["CellText"]),
        ])

    col_widths = [2.3 * cm, 4.2 * cm, _CONTENT_WIDTH - 2.3 * cm - 4.2 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE_COLOR),
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_COLOR]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _generic_table(header_labels: list[str], rows: list[list], col_widths: list[float]):
    """Tabla con cabecera oscura para listados (candidatos de typosquatting, canales de denuncia, cadena de custodia...)."""
    header = [Paragraph(h, _styles["CellTextWhite"]) for h in header_labels]
    body = [header] + rows
    table = Table(body, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE_COLOR),
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_COLOR]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _alert_box(text: str, kind: str = "warning", prefix: str | None = None) -> Table:
    """
    Aviso de una línea con una barra de color a la izquierda — sustituye a
    los emojis de advertencia (⚠) de la versión anterior, más propios de
    una notificación de app que de un documento técnico.
    """
    bg, accent = _ALERT_STYLES[kind]
    prefix = prefix or {"info": "Nota", "warning": "Aviso", "danger": "Atención"}[kind]
    cell = Paragraph(f"<b>{_xml_escape(prefix)}:</b> {text}", _styles["AlertText"])
    table = Table([[cell]], colWidths=[_CONTENT_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _score_banner(score: int) -> Table:
    color = _score_color(score)
    label = "RIESGO ALTO" if score >= 60 else "RIESGO MEDIO" if score >= 30 else "RIESGO BAJO"
    cell = Paragraph(f'<font color="white"><b>Score de riesgo: {score}/100 — {label}</b></font>', _styles["CellText"])
    table = Table([[cell]], colWidths=[_CONTENT_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _stat_tile(label: str, value: str, color) -> list:
    return [
        Paragraph(label.upper(), _styles["StatLabel"]),
        Paragraph(str(value), ParagraphStyle("StatValueColored", parent=_styles["StatValue"], textColor=color)),
    ]


def _stat_row(tiles: list[tuple[str, str, object]]) -> Table:
    """Tira de estadísticas tipo panel (casos incluidos, score máximo...) — visualmente distinta de las tablas etiqueta/valor repetidas por todo el documento, para que la portada no se sienta como "otra tabla más"."""
    cell_width = _CONTENT_WIDTH / len(tiles)
    row = [_stat_tile(label, value, color) for label, value, color in tiles]
    table = Table([row], colWidths=[cell_width] * len(tiles))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _LABEL_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, _LINE_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _LINE_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def _make_reference(now: datetime, case_ids: list[int]) -> str:
    """Código de referencia corto y determinista para el documento (útil para citarlo en una denuncia: 'informe SS-20260731-4F2A19')."""
    digest = hashlib.sha1(f"{now.isoformat()}|{','.join(str(i) for i in sorted(case_ids))}".encode()).hexdigest()[:6].upper()
    return f"SS-{now:%Y%m%d}-{digest}"


class _NumberedCanvas(_canvaslib.Canvas):
    """
    Difiere el dibujado del pie de página hasta `save()`, momento en el que
    ya se conoce cuántas páginas tiene el documento en total — así el pie
    puede decir "Página 3 de 8" en vez de solo "Página 3". Recibe las
    funciones de cabecera/pie ya cerradas sobre los datos del informe
    (fecha, referencia) para no depender de estado global.
    """
    def __init__(self, *args, header_fn=None, footer_fn=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._header_fn = header_fn
        self._footer_fn = footer_fn

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            page_num = self._pageNumber
            if page_num > 1 and self._header_fn:
                self._header_fn(self, page_num)
            if self._footer_fn:
                self._footer_fn(self, page_num, total_pages)
            super().showPage()
        super().save()


class _ReportDocTemplate(SimpleDocTemplate):
    """
    Subclase mínima necesaria para que el índice (`TableOfContents`) sepa en
    qué página cae cada sección/caso: cada vez que se dibuja un párrafo con
    estilo SectionHeading o SubHeading, se lo notifica al TOC y se añade un
    marcador de PDF nativo (visible en el panel de marcadores de cualquier
    lector de PDF), para poder saltar directamente a esa sección.
    """
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name == "SectionHeading":
            text = flowable.getPlainText()
            self.notify("TOCEntry", (0, text, self.page))
            key = f"toc-{self.page}-{id(flowable)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
        elif style_name == "SubHeading":
            text = flowable.getPlainText()
            self.notify("TOCEntry", (1, text, self.page))
            key = f"toc-{self.page}-{id(flowable)}"
            self.canv.bookmarkPage(key)


def _append_section(story: list, section_number: int, title: str, cases: list, builder) -> int:
    """
    Añade una sección numerada ("N. Título") con un caso por bloque. La
    cabecera de sección se mete DENTRO del KeepTogether del primer caso
    (ver docstring del módulo) — así nunca queda sola al final de una
    página. Devuelve el número de sección actualizado (0 si no había
    casos, para no numerar secciones vacías).
    """
    if not cases:
        return section_number
    section_number += 1
    heading = Paragraph(f"{section_number}. {title}", _styles["SectionHeading"])
    for i, case in enumerate(cases, start=1):
        block = builder(case, section_number, i)
        if heading is not None:
            block = [heading] + block
            heading = None
        story.append(KeepTogether(block))
        story.append(Spacer(1, 10))
    return section_number


# ============================================================
# Secciones por módulo — cada una devuelve una lista de flowables,
# envuelta en KeepTogether por _append_section (o directamente en
# build_report_pdf para las secciones que no son "un caso por bloque").
# ============================================================

def _domain_section(case: Case, section_number: int, index: int) -> list:
    whois = case.whois or {}
    ssl = case.ssl or {}
    vt = case.virustotal or {}
    dns = case.dns or {}
    flow = [
        Paragraph(f"{section_number}.{index} Dominio analizado: {_xml_escape(case.domain)}", _styles["SubHeading"]),
        Paragraph(f"Analizado el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
        _block(
            _field("Datos de registro (WHOIS)"),
            _kv_table([
                ("Registrador", whois.get("registrar")),
                ("Fecha de registro", whois.get("creation_date")),
                ("Antigüedad (días)", whois.get("domain_age_days")),
                ("País", whois.get("country")),
            ]),
        ),
        Spacer(1, 10),
        _block(
            _field("Certificado SSL"),
            _kv_table([
                ("Certificado válido", "Sí" if ssl.get("has_valid_cert") else "No"),
                ("Emisor", ssl.get("issuer")),
                ("Días desde la emisión", ssl.get("days_since_issued")),
            ]),
        ),
    ]
    if vt:
        flow += [
            Spacer(1, 10),
            _block(
                _field("VirusTotal (veredicto de la comunidad de seguridad)"),
                _kv_table([
                    ("Motores que lo marcan malicioso", vt.get("malicious_count", 0)),
                    ("Motores que lo marcan sospechoso", vt.get("suspicious_count", 0)),
                    ("Motores que no detectan nada", vt.get("undetected_count", 0)),
                    ("Categorías", ", ".join(vt.get("categories", [])) or None),
                ]),
            ),
        ]
    abuseipdb = case.abuseipdb or {}
    if abuseipdb:
        flow += [
            Spacer(1, 10),
            _block(
                _field(f"Reputación de la IP resuelta ({case.resolved_ip}) — AbuseIPDB"),
                _kv_table([
                    ("Puntuación de abuso", f"{abuseipdb.get('abuse_confidence_score', 0)}/100"),
                    ("Nº de reportes", abuseipdb.get("total_reports", 0)),
                    ("ISP", abuseipdb.get("isp")),
                    ("Tipo de uso", abuseipdb.get("usage_type")),
                    ("Nodo de salida Tor", "Sí" if abuseipdb.get("is_tor") else "No"),
                ]),
            ),
        ]
    other_ips = [e for e in (case.ip_reputations or []) if e.get("ip") != case.resolved_ip]
    if other_ips:
        flow += [
            Spacer(1, 10),
            _block(
                _field(f"Otras IPs resueltas ({len(other_ips)})"),
                _kv_table([
                    (e["ip"], f"{e['abuseipdb']['abuse_confidence_score']}/100 de abuso ({e['abuseipdb']['total_reports']} reportes)" if e.get("abuseipdb") else "sin datos AbuseIPDB")
                    for e in other_ips
                ]),
            ),
        ]
    if dns:
        has_mx = bool(dns.get("mx_hosts"))
        flow += [
            Spacer(1, 10),
            _block(
                _field("DNS"),
                _kv_table([
                    ("Servidores de correo (MX)", ", ".join(dns.get("mx_hosts", [])) or None),
                    ("SPF configurado", ("Sí" if dns.get("has_spf") else "No") if has_mx else "N/A (sin MX)"),
                    ("DMARC configurado", ("Sí" if dns.get("has_dmarc") else "No") if has_mx else "N/A (sin MX)"),
                    ("Registros CAA", len(dns.get("caa_records", [])) or "Ninguno"),
                ]),
            ),
        ]
    crtsh = case.crtsh or {}
    if crtsh:
        crtsh_block = [
            _field("Subdominios relacionados (Certificate Transparency — crt.sh)"),
            _kv_table([
                ("Subdominios encontrados", crtsh.get("subdomain_count", 0)),
                ("Ejemplos", ", ".join(crtsh.get("subdomains", [])[:8]) or None),
            ]),
        ]
        if crtsh.get("suspected_brand_subdomains"):
            crtsh_block += [Spacer(1, 4), _alert_box(
                "mencionan una marca conocida sin pertenecerle: " + _xml_escape(", ".join(crtsh["suspected_brand_subdomains"])),
                kind="danger",
            )]
        flow += [Spacer(1, 10), _block(*crtsh_block)]
    wayback = case.wayback or {}
    if wayback:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Historial (Wayback Machine)"),
                _kv_table([
                    ("Capturas totales", wayback.get("total_snapshots", 0)),
                    ("Primera captura", wayback.get("first_snapshot")),
                    ("Última captura", wayback.get("last_snapshot")),
                ]),
            ),
        ]
    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _email_section(case: EmailCase, section_number: int, index: int) -> list:
    headers = case.headers or {}
    flow = [
        Paragraph(f"{section_number}.{index} Email analizado: {_xml_escape(headers.get('subject') or '(sin asunto)')}", _styles["SubHeading"]),
        Paragraph(f"Analizado el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
    ]
    if case.is_raw_source is False:
        flow += [
            _alert_box(
                "no se pudo verificar el código fuente técnico de este email (el texto proporcionado no traía "
                "cabeceras como Received o Authentication-Results); SPF/DKIM/DMARC no se comprobaron.",
                kind="info",
            ),
            Spacer(1, 8),
        ]
    flow += [
        _block(
            _field("Cabeceras del mensaje"),
            _kv_table([
                ("Remitente", headers.get("from_address")),
                ("Nombre mostrado", headers.get("from_display_name")),
                ("Responder a", headers.get("reply_to")),
                ("Ruta de retorno", headers.get("return_path")),
                ("SPF", headers.get("spf_result")),
                ("DKIM", headers.get("dkim_result")),
                ("DMARC", headers.get("dmarc_result")),
                ("IP de origen", headers.get("originating_ip")),
            ]),
        ),
    ]
    ip_abuse = case.originating_ip_abuseipdb or {}
    if ip_abuse:
        flow += [
            Spacer(1, 10),
            _block(
                _field(f"Reputación de la IP de origen ({headers.get('originating_ip')}) — AbuseIPDB"),
                _kv_table([
                    ("Puntuación de abuso", f"{ip_abuse.get('abuse_confidence_score', 0)}/100"),
                    ("Nº de reportes", ip_abuse.get("total_reports", 0)),
                    ("ISP", ip_abuse.get("isp")),
                    ("Nodo de salida Tor", "Sí" if ip_abuse.get("is_tor") else "No"),
                ]),
            ),
        ]
    if case.links:
        rows = []
        for link in case.links:
            dest = link.get("redirects_to") or link.get("domain") or ""
            note_parts = []
            if link.get("is_shortener"):
                note_parts.append("acortador")
            if link.get("suspected_brand"):
                note_parts.append(f"imita a '{link['suspected_brand']}'")
            if link.get("virustotal_malicious_count"):
                note_parts.append(f"{link['virustotal_malicious_count']} motores VT en rojo")
            note = f"{dest} — {', '.join(note_parts) if note_parts else 'sin más notas'}"
            # Las URLs reales llevan '&' con frecuencia (parámetros de tracking); sin
            # escapar rompería el parseo XML interno de reportlab al generar el PDF.
            rows.append((_xml_escape(link.get("url") or ""), _xml_escape(note)))
        flow += [
            Spacer(1, 10),
            _block(
                _field(f"Enlaces del cuerpo ({len(case.links)})"),
                _kv_table(rows),
            ),
        ]
    if case.attachments:
        rows = [
            (_xml_escape(att.get("filename") or ""), _xml_escape(
                f"{att.get('size_bytes', 0)} bytes · sha256 {att.get('sha256', '')[:16]}…"
                + (" · EXTENSIÓN PELIGROSA" if att.get("is_dangerous_extension") else "")
                + (" · DOBLE EXTENSIÓN" if att.get("has_double_extension") else "")
            ))
            for att in case.attachments
        ]
        flow += [
            Spacer(1, 10),
            _block(
                _field(f"Adjuntos ({len(case.attachments)})"),
                _kv_table(rows),
            ),
        ]
    if case.ai_explanation:
        flow += [Spacer(1, 10), _alert_box(_xml_escape(case.ai_explanation), kind="info", prefix="Explicación (IA)")]
    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _wallet_section(case: WalletCase, section_number: int, index: int) -> list:
    wallet = case.wallet or {}
    flow = [
        Paragraph(f"{section_number}.{index} Wallet analizada: {_xml_escape(case.address)} ({case.chain})", _styles["SubHeading"]),
        Paragraph(f"Analizada el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
        _block(
            _field("Actividad de la wallet"),
            _kv_table([
                ("Nº de transacciones analizadas", wallet.get("n_transactions")),
                ("Total recibido", f"{wallet.get('total_received')} {case.chain}"),
                ("Total enviado", f"{wallet.get('total_sent')} {case.chain}"),
                ("Balance actual", f"{wallet.get('balance')} {case.chain}"),
                ("Primera transacción", wallet.get("first_transaction_at")),
                ("Remitentes distintos (muestra reciente)", wallet.get("unique_senders_recent")),
            ]),
        ),
    ]
    if wallet.get("note"):
        flow += [Spacer(1, 6), Paragraph(f"Nota: {_xml_escape(wallet['note'])}", _styles["SmallGray"])]
    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _typosquatting_section(case: TyposquattingCase, section_number: int, index: int) -> list:
    candidates = case.candidates or []
    flow = [
        Paragraph(f"{section_number}.{index} Marca protegida: {_xml_escape(case.domain)}", _styles["SubHeading"]),
        Paragraph(f"Analizado el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
        _block(
            _field("Exposición a suplantación de dominio"),
            _kv_table([
                ("Variantes generadas y comprobadas", case.variants_generated),
                ("Variantes activas encontradas", case.resolved_count),
            ]),
        ),
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    if candidates:
        rows = []
        for c in candidates:
            score_txt = (
                f"{c['risk_score']} ({'completo' if c.get('fully_analyzed') else 'IP'})"
                if c.get("risk_score") is not None else "sin analizar"
            )
            rows.append([
                Paragraph(_xml_escape(c.get("variant", "")), _styles["CellText"]),
                Paragraph(_xml_escape(c.get("technique", "")), _styles["CellText"]),
                Paragraph(_xml_escape(c.get("ip_address") or "—"), _styles["CellText"]),
                Paragraph(score_txt, _styles["CellText"]),
            ])
        col_widths = [6 * cm, 3.5 * cm, 3.2 * cm, _CONTENT_WIDTH - 6 * cm - 3.5 * cm - 3.2 * cm]
        flow += [
            Spacer(1, 10),
            _field("Dominios activos encontrados"),
            _generic_table(["Dominio", "Técnica", "IP", "Score"], rows, col_widths),
        ]  # sin _block: puede ser una tabla larga (docenas de variantes) — repeatRows=1 ya repite la cabecera al partirse entre páginas, comportamiento correcto para una tabla de verdad larga
    return flow


def _phone_section(case: PhoneCase, section_number: int, index: int) -> list:
    phone = case.phone or {}
    community = case.community_reports or {}
    fraud = case.fraud_score or {}
    carrier_intel = case.carrier_intelligence or {}
    flow = [
        Paragraph(f"{section_number}.{index} Teléfono analizado: {_xml_escape(phone.get('international_format') or case.raw_phone)}", _styles["SubHeading"]),
        Paragraph(f"Analizado el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
        _block(
            _field("Datos del número"),
            _kv_table([
                ("Formato internacional", phone.get("international_format")),
                ("País", phone.get("country_name")),
                ("Operador", phone.get("carrier")),
                ("Tipo de línea", phone.get("line_type")),
                ("Formato válido", "Sí" if phone.get("is_valid") else "No"),
            ]),
        ),
    ]
    if community:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Reportes de la comunidad (OpenSpam)"),
                _kv_table([
                    ("Nº de reportes", community.get("reports_count", 0)),
                    ("Categoría", community.get("category")),
                    ("Provincia", community.get("province")),
                    ("Nivel de peligro reportado", community.get("danger_level")),
                ]),
            ),
        ]
    if fraud:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Puntuación de fraude (IPQualityScore)"),
                _kv_table([
                    ("Fraud score", f"{fraud['fraud_score']}/100" if fraud.get("fraud_score") is not None else None),
                    ("VOIP", "Sí" if fraud.get("voip") else "No"),
                    ("Prepago", "Sí" if fraud.get("prepaid") else "No"),
                    ("Abuso reciente reportado", "Sí" if fraud.get("recent_abuse") else "No"),
                    ("Filtrado en alguna brecha de datos", "Sí" if fraud.get("leaked") else "No"),
                ]),
            ),
        ]
    if carrier_intel:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Carrier en tiempo real (Twilio Lookup)"),
                _kv_table([
                    ("Operador", carrier_intel.get("carrier_name")),
                    ("Tipo de línea (en vivo)", carrier_intel.get("line_type")),
                ]),
            ),
        ]
    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _cnmv_section(case: CnmvCheckCase, section_number: int, index: int) -> list:
    flow = [
        Paragraph(f"{section_number}.{index} Verificación CNMV: \"{_xml_escape(case.query)}\"", _styles["SubHeading"]),
        Paragraph(f"Consultado el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
    ]
    matches = case.matches or []
    if matches:
        label = _field(f"Se encontraron {len(matches)} advertencia(s) pública(s) de la CNMV")
        for m in matches:
            table = _kv_table([
                ("Fecha de la advertencia", m.get("fecha")),
                ("Entidad(es) advertida(s)", (m.get("companias") or "").replace("\n", "<br/>")),
                ("Observaciones", m.get("observaciones")),
            ])
            # Cada advertencia va con su propia etiqueta de "campo" para no quedar suelta al partirse la página;
            # solo la primera lleva la etiqueta general de la subsección.
            flow.append(_block(label, table) if label else _block(table))
            flow.append(Spacer(1, 6))
            label = None
    else:
        flow.append(Paragraph("No se encontraron coincidencias en el listado de advertencias de la CNMV para esta búsqueda.", _styles["SmallGray"]))

    fca_matches = case.fca_matches or []
    if fca_matches:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Registro de la FCA (Reino Unido) — comprobación en positivo"),
                _kv_table([
                    (m.get("name"), f"{m.get('status')} · {m.get('reference_number')}")
                    for m in fca_matches
                ]),
            ),
        ]

    registry_matches = case.registry_matches
    if registry_matches is not None:
        registry_content = (
            _kv_table([(m.get("name"), m.get("code")) for m in registry_matches])
            if registry_matches
            else Paragraph("No se ha encontrado ninguna entidad con este nombre en el registro.", _styles["SmallGray"])
        )
        flow += [
            Spacer(1, 10),
            _block(_field("Registro de entidades autorizadas de la CNMV — comprobación en positivo"), registry_content),
        ]

    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _ip_section(case: IpCase, section_number: int, index: int) -> list:
    abuse = case.abuseipdb or {}
    flow = [
        Paragraph(f"{section_number}.{index} IP analizada: {case.ip}", _styles["SubHeading"]),
        Paragraph(f"Analizada el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
    ]
    if abuse:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Reputación (AbuseIPDB)"),
                _kv_table([
                    ("Puntuación de abuso", f"{abuse.get('abuse_confidence_score', 0)}/100"),
                    ("Nº de reportes", abuse.get("total_reports", 0)),
                    ("ISP", abuse.get("isp")),
                    ("Tipo de uso", abuse.get("usage_type")),
                    ("País", abuse.get("country_code")),
                    ("Nodo de salida Tor", "Sí" if abuse.get("is_tor") else "No"),
                ]),
            ),
        ]
    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


def _image_section(
    case: ImageCase,
    section_number: int,
    index: int,
    reverse_search: ReverseImageSearchCase | None = None,
    facial_search: FacialSearchCase | None = None,
) -> list:
    exif = case.exif or {}
    matches = case.matches or []
    flow = [
        Paragraph(f"{section_number}.{index} Imagen analizada: {_xml_escape(case.filename or '(sin nombre)')}", _styles["SubHeading"]),
        Paragraph(f"Analizada el {case.analyzed_at:%d/%m/%Y %H:%M} UTC · Caso #{case.id}", _styles["SmallGray"]),
        Spacer(1, 6),
        _score_banner(case.risk_score),
        Spacer(1, 10),
        _block(
            _field("Metadatos (EXIF)"),
            _kv_table([
                ("Tiene metadatos", "Sí" if exif.get("has_exif") else "No"),
                ("Cámara", " ".join(filter(None, [exif.get("camera_make"), exif.get("camera_model")])) or None),
                ("Software", exif.get("software")),
                ("Fecha original", exif.get("date_taken")),
                ("GPS", f"{exif['gps_latitude']}, {exif['gps_longitude']}" if exif.get("gps_latitude") else None),
            ]),
        ),
    ]
    if matches:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Imagen ya vista en otros casos de esta herramienta"),
                _kv_table([
                    (f"Caso #{m['case_id']} ({m.get('filename') or 'sin nombre'})", f"{m['similarity_percent']}% de similitud")
                    for m in matches
                ]),
            ),
        ]

    if reverse_search and reverse_search.matches:
        flow += [
            Spacer(1, 10),
            _block(
                _field("Búsqueda inversa en internet (SerpApi)"),
                _kv_table([
                    (m.get("source") or m.get("page_title") or "Página externa", m["url"])
                    for m in reverse_search.matches
                ]),
            ),
        ]

    if facial_search:
        facial_block = [
            _field("Búsqueda de reconocimiento facial (PimEyes)"),
            Paragraph(
                "Esta búsqueda procesa un dato biométrico y se ejecutó como acción separada y "
                f"confirmada explícitamente el {facial_search.requested_at:%d/%m/%Y %H:%M} UTC. "
                "Los resultados NO son prueba automática de identidad robada — requieren revisión "
                "humana para confirmar si corresponden a un perfil/nombre distinto.",
                _styles["SmallGray"],
            ),
        ]
        if facial_search.notes:
            facial_block.append(Paragraph(f"Notas registradas: {_xml_escape(facial_search.notes)}", _styles["SmallGray"]))
        if facial_search.matches:
            facial_block += [
                Spacer(1, 4),
                _kv_table([
                    (m.get("page_title") or "Página externa", m["url"])
                    for m in facial_search.matches
                ]),
            ]
        flow += [Spacer(1, 10), _block(*facial_block)]

    flow += [
        Spacer(1, 10),
        _block(
            _field("Señales de riesgo detectadas"),
            _flags_table(case.risk_flags),
        ),
    ]
    return flow


# ============================================================
# Documento completo
# ============================================================

def build_report_pdf(
    domain_cases: list[Case],
    email_cases: list[EmailCase],
    wallet_cases: list[WalletCase],
    victim_notes: str | None = None,
    ai_narrative: str | None = None,
    typosquatting_cases: list[TyposquattingCase] | None = None,
    phone_cases: list[PhoneCase] | None = None,
    cnmv_cases: list[CnmvCheckCase] | None = None,
    image_cases: list[ImageCase] | None = None,
    ledger_entries: list | None = None,
    chain_intact: bool | None = None,
    reporting_channels: list | None = None,
    reverse_image_search_cases: list[ReverseImageSearchCase] | None = None,
    facial_search_cases: list[FacialSearchCase] | None = None,
    ip_cases: list[IpCase] | None = None,
) -> bytes:
    typosquatting_cases = typosquatting_cases or []
    phone_cases = phone_cases or []
    cnmv_cases = cnmv_cases or []
    image_cases = image_cases or []
    ip_cases = ip_cases or []
    ledger_entries = ledger_entries or []
    reporting_channels = reporting_channels or []
    # La más reciente gana si hubiera más de una búsqueda para el mismo caso de imagen.
    reverse_search_by_image_case = {c.image_case_id: c for c in (reverse_image_search_cases or [])}
    facial_search_by_image_case = {c.image_case_id: c for c in (facial_search_cases or [])}

    now = datetime.now(timezone.utc)
    all_cases = (*domain_cases, *email_cases, *wallet_cases, *typosquatting_cases, *phone_cases, *cnmv_cases, *image_cases, *ip_cases)
    all_scores = [c.risk_score for c in all_cases]
    max_score = max(all_scores) if all_scores else 0
    reference = _make_reference(now, [c.id for c in all_cases])
    module_count = sum(1 for cases in (domain_cases, email_cases, wallet_cases, typosquatting_cases, phone_cases, cnmv_cases, image_cases, ip_cases) if cases)

    buffer = BytesIO()
    doc = _ReportDocTemplate(
        buffer, pagesize=A4,
        topMargin=_PAGE_MARGIN, bottomMargin=_PAGE_MARGIN, leftMargin=_PAGE_MARGIN, rightMargin=_PAGE_MARGIN,
        title=f"Informe de evidencias — ScamShield — {reference}",
    )

    def _draw_header(canvas_obj, _page_num):
        canvas_obj.saveState()
        canvas_obj.setStrokeColor(_ACCENT_COLOR)
        canvas_obj.setLineWidth(1.6)
        canvas_obj.line(_PAGE_MARGIN, A4[1] - 1.35 * cm, A4[0] - _PAGE_MARGIN, A4[1] - 1.35 * cm)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(_MUTED_TEXT)
        canvas_obj.drawString(_PAGE_MARGIN, A4[1] - 1.15 * cm, "Informe de evidencias de posible fraude — ScamShield")
        canvas_obj.drawRightString(A4[0] - _PAGE_MARGIN, A4[1] - 1.15 * cm, f"Ref. {reference}")
        canvas_obj.restoreState()

    def _draw_footer(canvas_obj, page_num, total_pages):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(_MUTED_TEXT)
        canvas_obj.drawString(_PAGE_MARGIN, 1.3 * cm, f"Generado el {now:%d/%m/%Y %H:%M} UTC")
        canvas_obj.drawRightString(A4[0] - _PAGE_MARGIN, 1.3 * cm, f"Página {page_num} de {total_pages}")
        canvas_obj.restoreState()

    def _numbered_canvas(*args, **kwargs):
        return _NumberedCanvas(*args, header_fn=_draw_header, footer_fn=_draw_footer, **kwargs)

    story = []

    # --- Portada ---
    story.append(Paragraph("INFORME TÉCNICO DE EVIDENCIAS", _styles["Kicker"]))
    story.append(Paragraph("Evidencia técnica de posible fraude", _styles["ReportTitle"]))
    story.append(Paragraph("Generado automáticamente con ScamShield", _styles["CoverMeta"]))
    story.append(Paragraph(f"Referencia: {reference} · {now:%d/%m/%Y %H:%M} UTC", _styles["CoverMeta"]))
    story.append(Spacer(1, 14))

    story.append(_alert_box(
        "este documento se ha generado de forma automatizada a partir de fuentes públicas y APIs de "
        "reputación. No constituye un dictamen pericial ni sustituye la valoración de las autoridades "
        "competentes; su objetivo es organizar la evidencia técnica disponible para facilitar su "
        "presentación junto con una denuncia.",
        kind="info",
    ))
    story.append(Spacer(1, 16))

    stat_tiles = [
        ("Casos incluidos", str(len(all_cases)), _BRAND_COLOR),
        ("Módulos incluidos", str(module_count), _BRAND_COLOR),
        ("Score máximo", f"{max_score}/100", _score_color(max_score)),
    ]
    if ledger_entries:
        stat_tiles.append(
            ("Cadena de custodia", "Íntegra" if chain_intact else "Rota", _SEVERITY_COLORS["low"] if chain_intact else _SEVERITY_COLORS["high"])
        )
    story.append(_stat_row(stat_tiles))
    story.append(Spacer(1, 10))

    breakdown = (
        f"{len(domain_cases)} dominio(s), {len(email_cases)} email(s), {len(wallet_cases)} wallet(s), "
        f"{len(typosquatting_cases)} typosquatting, {len(phone_cases)} teléfono(s), {len(cnmv_cases)} verificación(es) CNMV, "
        f"{len(image_cases)} imagen(es), {len(ip_cases)} IP(s)"
    )
    story.append(Paragraph(f"<b>Desglose por módulo:</b> {breakdown}", _styles["CoverMeta"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        "Este documento recopila de forma automatizada evidencia técnica pública (registro de dominios, "
        "cabeceras de correo, movimientos de wallets en blockchains públicas, variantes de dominio activas) "
        "relacionada con una posible estafa.",
        _styles["BodyText2"],
    ))

    if ai_narrative:
        story.append(Spacer(1, 14))
        story.append(_field("Valoración consolidada"))
        story.append(Paragraph(ai_narrative, _styles["BodyText2"]))

    if victim_notes:
        story.append(Spacer(1, 14))
        story.append(_field("Relato de los hechos (aportado por la persona afectada)"))
        story.append(Paragraph(victim_notes.replace("\n", "<br/>"), _styles["BodyText2"]))

    story.append(PageBreak())

    # --- Índice ---
    story.append(Paragraph("Índice", _styles["TOCHeading"]))
    toc = TableOfContents()
    toc.levelStyles = [_styles["TOCLevel0"], _styles["TOCLevel1"]]
    story.append(toc)
    story.append(PageBreak())

    # --- Secciones por módulo ---
    section_number = 0
    section_number = _append_section(story, section_number, "Análisis de dominios", domain_cases, _domain_section)
    section_number = _append_section(story, section_number, "Análisis de emails", email_cases, _email_section)
    section_number = _append_section(story, section_number, "Análisis de wallets cripto", wallet_cases, _wallet_section)
    section_number = _append_section(story, section_number, "Detección de typosquatting", typosquatting_cases, _typosquatting_section)
    section_number = _append_section(story, section_number, "Análisis de teléfonos", phone_cases, _phone_section)
    section_number = _append_section(story, section_number, "Verificación de entidades (CNMV)", cnmv_cases, _cnmv_section)
    section_number = _append_section(
        story, section_number, "Análisis de imágenes", image_cases,
        lambda case, sn, i: _image_section(
            case, sn, i,
            reverse_search_by_image_case.get(case.id),
            facial_search_by_image_case.get(case.id),
        ),
    )
    section_number = _append_section(story, section_number, "Análisis de IPs", ip_cases, _ip_section)

    if reporting_channels:
        section_number += 1
        rows = [[
            Paragraph(_xml_escape(ch.name), _styles["CellTextBold"]),
            Paragraph(_xml_escape(ch.when_to_use), _styles["CellText"]),
            Paragraph(f'<link href="{_xml_escape(ch.url)}">{_xml_escape(ch.url)}</link>', _styles["CellText"]),
        ] for ch in reporting_channels]
        col_widths = [4.5 * cm, 7.2 * cm, _CONTENT_WIDTH - 4.5 * cm - 7.2 * cm]
        block = [
            Paragraph(f"{section_number}. Dónde denunciar", _styles["SectionHeading"]),
            _generic_table(["Organismo", "Cuándo usarlo", "Enlace"], rows, col_widths),
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 14))

    if ledger_entries:
        section_number += 1
        status_kind = "info" if chain_intact else "danger"
        status_txt = "cadena íntegra, sin manipulaciones detectadas." if chain_intact else "CADENA ROTA — se ha detectado una manipulación en algún registro."
        rows = [[
            Paragraph(e.case_type, _styles["CellText"]),
            Paragraph(f"#{e.case_id}", _styles["CellText"]),
            Paragraph(e.evidence_hash, _styles["SmallGray"]),
            Paragraph(f"{e.captured_at:%d/%m/%Y %H:%M} UTC", _styles["CellText"]),
        ] for e in ledger_entries]
        col_widths = [2.5 * cm, 2 * cm, _CONTENT_WIDTH - 2.5 * cm - 2 * cm - 3 * cm, 3 * cm]
        block = [
            Paragraph(f"{section_number}. Certificado de integridad de la evidencia", _styles["SectionHeading"]),
            _alert_box(status_txt, kind=status_kind, prefix="Estado"),
            Spacer(1, 8),
            _generic_table(["Tipo", "Caso", "Huella SHA-256", "Capturado"], rows, col_widths),
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 14))

    doc.multiBuild(story, canvasmaker=_numbered_canvas)
    return buffer.getvalue()
