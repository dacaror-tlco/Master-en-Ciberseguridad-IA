"""
Servicio de inspección de certificados SSL.

Se conecta directamente al puerto 443 del dominio y lee el certificado
que presenta, sin depender de ninguna API externa de pago.
Un certificado emitido hace muy pocos días es una señal de riesgo típica
(los estafadores montan el sitio y el certificado justo antes de operar).
"""
import socket
import ssl
from datetime import datetime, timezone

from app.schemas.domain_analysis import SSLCertInfo

# Formato de fecha que usan los certificados X.509
_CERT_DATE_FMT = "%b %d %H:%M:%S %Y %Z"


def get_ssl_info(domain: str, timeout: float = 5.0) -> SSLCertInfo:
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()

    issuer_parts = dict(x[0] for x in cert.get("issuer", []))
    issuer = issuer_parts.get("organizationName") or issuer_parts.get("commonName")

    issued_date = None
    days_since_issued = None
    not_before = cert.get("notBefore")
    if not_before:
        issued_date = datetime.strptime(not_before, _CERT_DATE_FMT).replace(tzinfo=timezone.utc)
        days_since_issued = (datetime.now(timezone.utc) - issued_date).days

    alt_names = [entry[1] for entry in cert.get("subjectAltName", []) if entry[0] == "DNS"]

    return SSLCertInfo(
        has_valid_cert=True,
        issuer=issuer,
        issued_date=issued_date,
        days_since_issued=days_since_issued,
        subject_alt_names=alt_names,
    )
