"""
Servicio de parseo de emails: cabeceras, cuerpo (enlaces) y adjuntos.

Trabajamos sobre el email "crudo" (raw source), no sobre el texto que se ve
en el cliente de correo. Las cabeceras son las que no se pueden falsificar
tan fácilmente sin dejar rastro: quién dice ser el remitente (From) puede
mentir, pero la cadena de servidores por los que pasó el mensaje (Received)
y los resultados de autenticación (SPF/DKIM/DMARC) son mucho más difíciles
de falsificar sin que se note.

No todo el mundo consigue (o sabe) exportar el código fuente real de un
email: alguien en shock tras un intento de estafa puede limitarse a pegar
el texto que ve en pantalla. `looks_like_raw_source` distingue ambos casos
para que el resto del pipeline pueda degradar con gracia (seguir
analizando enlaces/adjuntos/contenido aunque no haya cabeceras técnicas
que verificar) en vez de fallar o dar señales SPF/DKIM engañosas.
"""
import hashlib
import re
from email import message_from_string
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime

from bs4 import BeautifulSoup

from app.schemas.email_analysis import EmailAttachmentInfo, EmailHeaderInfo

_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_URL_PATTERN = re.compile(r"https?://[^\s<>\"'\)\]]+", re.IGNORECASE)

# Extensiones capaces de ejecutar código si la víctima las abre. No es una
# lista exhaustiva de malware, es "esto nunca debería llegar por email de
# alguien que dice ser tu banco/empresa de paquetería".
_DANGEROUS_EXTENSIONS = {
    "exe", "scr", "bat", "cmd", "com", "pif", "vbs", "vbe", "js", "jse",
    "wsf", "wsh", "ps1", "psm1", "jar", "lnk", "msi", "reg",
    "docm", "xlsm", "pptm", "iso", "img",
}
# Extensiones "de confianza" habituales como primer tramo de una doble
# extensión (factura.pdf.exe): si el nombre las lleva justo antes de una
# extensión peligrosa, es la técnica clásica de disfrazar un ejecutable.
_BENIGN_LOOKING_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg",
    "png", "gif", "txt", "zip",
}


def parse_email_message(raw_email: str) -> Message:
    return message_from_string(raw_email)


def looks_like_raw_source(msg: Message) -> bool:
    """
    Heurística: un email exportado como código fuente real siempre trae
    al menos una de estas cabeceras, añadidas por los servidores por los
    que pasó (no por el cliente de correo). Si no hay ninguna, lo más
    probable es que el usuario haya pegado el texto visible del mensaje
    (o un fragmento incompleto), no el raw source.
    """
    return bool(
        msg.get_all("Received")
        or msg.get("Message-ID")
        or msg.get_all("Authentication-Results")
    )


def _extract_auth_result(auth_results_header: str, mechanism: str) -> str | None:
    """
    Busca 'spf=pass', 'dkim=fail', 'dmarc=none', etc. dentro de la cabecera
    Authentication-Results, que es la que añade el servidor receptor
    (Gmail, Outlook...) tras comprobar la autenticidad del email.
    """
    match = re.search(rf"{mechanism}=(\w+)", auth_results_header, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _extract_domain(address: str | None) -> str | None:
    if not address or "@" not in address:
        return None
    return address.rsplit("@", 1)[-1].lower().strip(">")


def parse_email_headers(raw_email: str) -> EmailHeaderInfo:
    return parse_email_headers_from_message(parse_email_message(raw_email))


def parse_email_headers_from_message(msg: Message) -> EmailHeaderInfo:
    from_header = msg.get("From", "")
    from_pairs = getaddresses([from_header])
    from_display_name, from_address = (from_pairs[0] if from_pairs else (None, None))

    reply_to_pairs = getaddresses([msg.get("Reply-To", "")])
    reply_to = reply_to_pairs[0][1] if reply_to_pairs and reply_to_pairs[0][1] else None

    return_path_pairs = getaddresses([msg.get("Return-Path", "")])
    return_path = return_path_pairs[0][1] if return_path_pairs and return_path_pairs[0][1] else None

    date = None
    if msg.get("Date"):
        try:
            date = parsedate_to_datetime(msg.get("Date"))
        except (TypeError, ValueError):
            date = None

    # Puede haber varias cabeceras Authentication-Results (una por cada
    # servidor intermedio); nos quedamos con todas concatenadas para buscar.
    auth_headers = " | ".join(msg.get_all("Authentication-Results", []))
    spf_result = _extract_auth_result(auth_headers, "spf")
    dkim_result = _extract_auth_result(auth_headers, "dkim")
    dmarc_result = _extract_auth_result(auth_headers, "dmarc")

    received_headers = msg.get_all("Received", [])
    received_hop_count = len(received_headers)

    # El origen real suele estar en el ÚLTIMO 'Received' (el primero
    # cronológicamente, añadido por el primer servidor que recibió el email).
    originating_ip = None
    if received_headers:
        ips_in_last_hop = _IP_PATTERN.findall(received_headers[-1])
        if ips_in_last_hop:
            originating_ip = ips_in_last_hop[-1]

    return EmailHeaderInfo(
        from_address=from_address or None,
        from_display_name=from_display_name or None,
        reply_to=reply_to,
        return_path=return_path,
        subject=msg.get("Subject"),
        date=date,
        spf_result=spf_result,
        dkim_result=dkim_result,
        dmarc_result=dmarc_result,
        originating_ip=originating_ip,
        received_hop_count=received_hop_count,
    )


def _iter_body_parts(msg: Message):
    """Recorre las partes text/plain y text/html del cuerpo (ignora adjuntos)."""
    if msg.is_multipart():
        parts = msg.walk()
    else:
        parts = [msg]

    for part in parts:
        if part.is_multipart():
            continue
        if part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            text = payload.decode("utf-8", errors="replace")
        yield content_type, text


def extract_links(msg: Message) -> list[str]:
    """
    Extrae todas las URLs del cuerpo del mensaje: los `href` de los enlaces
    en la versión HTML (lo que la víctima realmente pulsaría) y las URLs
    sueltas que aparezcan como texto plano. Deduplicadas, conservando el
    orden de aparición.
    """
    urls: list[str] = []
    seen: set[str] = set()

    def _add(url: str):
        url = url.strip().rstrip(".,;")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    for content_type, text in _iter_body_parts(msg):
        if content_type == "text/html":
            soup = BeautifulSoup(text, "html.parser")
            for a in soup.find_all("a", href=True):
                if a["href"].lower().startswith(("http://", "https://")):
                    _add(a["href"])
            # Además de los <a>, un correo de phishing simple puede llevar
            # URLs sueltas en el HTML sin marcar como enlace.
            for match in _URL_PATTERN.findall(soup.get_text(" ")):
                _add(match)
        else:
            for match in _URL_PATTERN.findall(text):
                _add(match)

    return urls


def _has_double_extension(filename: str) -> bool:
    parts = filename.lower().rsplit(".", 2)
    if len(parts) < 3:
        return False
    _, first_ext, last_ext = parts
    return first_ext in _BENIGN_LOOKING_EXTENSIONS and last_ext in _DANGEROUS_EXTENSIONS


def extract_attachments(msg: Message) -> list[EmailAttachmentInfo]:
    """Lista los adjuntos del mensaje con su huella, sin guardar el contenido en sí."""
    attachments: list[EmailAttachmentInfo] = []
    if not msg.is_multipart():
        return attachments

    for part in msg.walk():
        filename = part.get_filename()
        if not filename or part.get_content_disposition() != "attachment":
            continue

        payload = part.get_payload(decode=True) or b""
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else None

        attachments.append(EmailAttachmentInfo(
            filename=filename,
            extension=extension,
            size_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            is_dangerous_extension=extension in _DANGEROUS_EXTENSIONS if extension else False,
            has_double_extension=_has_double_extension(filename),
        ))

    return attachments
