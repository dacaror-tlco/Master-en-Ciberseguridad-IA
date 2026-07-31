"""
Tests de la extracción de cuerpo (enlaces) y adjuntos, y de la detección
de si el texto pegado es código fuente real o solo texto visible.
"""
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.email_service import (
    extract_attachments,
    extract_links,
    looks_like_raw_source,
    parse_email_message,
)
from tests.conftest import LEGIT_EMAIL_RAW, PHISHING_EMAIL_RAW

PLAIN_TEXT_PASTE = """
Estimado cliente,

Hemos detectado un acceso no autorizado a su cuenta. Verifique sus datos
en el siguiente enlace antes de 24 horas o su cuenta será bloqueada.

Un saludo, el equipo de soporte.
"""


def _html_email(html_body: str) -> str:
    msg = MIMEMultipart("alternative")
    msg["From"] = "Banco Seguro <soporte@banco-seguro-verificacion.xyz>"
    msg["Subject"] = "Verifica tu cuenta"
    msg.attach(MIMEText("Versión en texto plano, sin enlaces.", "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg.as_string()


def _email_with_attachment(filename: str, content: bytes = b"contenido de prueba") -> str:
    msg = MIMEMultipart()
    msg["From"] = "Envios <no-reply@paqueteria-legitima.com>"
    msg["Subject"] = "Tu paquete"
    msg.attach(MIMEText("Cuerpo del mensaje.", "plain"))
    part = MIMEApplication(content, Name=filename)
    part["Content-Disposition"] = f'attachment; filename="{filename}"'
    msg.attach(part)
    return msg.as_string()


def test_looks_like_raw_source_true_para_email_con_cabeceras_tecnicas():
    msg = parse_email_message(PHISHING_EMAIL_RAW)
    assert looks_like_raw_source(msg) is True


def test_looks_like_raw_source_false_para_texto_pegado_sin_cabeceras():
    msg = parse_email_message(PLAIN_TEXT_PASTE)
    assert looks_like_raw_source(msg) is False


def test_extract_links_de_html_incluye_href_y_deduplica():
    raw = _html_email(
        '<p>Pulsa <a href="https://banco-seguro-verificacion.xyz/login">aquí</a> '
        'o visita <a href="https://banco-seguro-verificacion.xyz/login">este otro enlace igual</a> '
        'o <a href="https://bit.ly/abc123">este acortado</a>.</p>'
    )
    msg = parse_email_message(raw)
    links = extract_links(msg)
    assert links == [
        "https://banco-seguro-verificacion.xyz/login",
        "https://bit.ly/abc123",
    ]


def test_extract_links_ignora_enlaces_no_http():
    raw = _html_email('<p><a href="mailto:soporte@banco.com">contacto</a></p>')
    msg = parse_email_message(raw)
    assert extract_links(msg) == []


def test_extract_attachments_detecta_extension_peligrosa():
    raw = _email_with_attachment("factura.exe")
    msg = parse_email_message(raw)
    attachments = extract_attachments(msg)
    assert len(attachments) == 1
    att = attachments[0]
    assert att.filename == "factura.exe"
    assert att.extension == "exe"
    assert att.is_dangerous_extension is True
    assert att.has_double_extension is False
    assert len(att.sha256) == 64


def test_extract_attachments_detecta_doble_extension():
    raw = _email_with_attachment("factura.pdf.exe")
    msg = parse_email_message(raw)
    attachments = extract_attachments(msg)
    assert attachments[0].has_double_extension is True


def test_extract_attachments_no_marca_pdf_normal_como_peligroso():
    raw = _email_with_attachment("factura.pdf")
    msg = parse_email_message(raw)
    attachments = extract_attachments(msg)
    assert attachments[0].is_dangerous_extension is False
    assert attachments[0].has_double_extension is False


def test_email_sin_adjuntos_da_lista_vacia():
    msg = parse_email_message(LEGIT_EMAIL_RAW)
    assert extract_attachments(msg) == []
    assert extract_links(msg) == []
