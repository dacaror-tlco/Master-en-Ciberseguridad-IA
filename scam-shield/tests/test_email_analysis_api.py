from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

from tests.conftest import LEGIT_EMAIL_RAW, PHISHING_EMAIL_RAW

PLAIN_TEXT_PASTE = """
Estimado cliente,

Hemos detectado un acceso no autorizado a su cuenta. Verifique sus datos
antes de 24 horas o su cuenta sera bloqueada.

Un saludo, el equipo de soporte.
"""


def test_analizar_email_por_archivo(client, fresh_whois):
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=fresh_whois):
        files = {"file": ("phishing.eml", PHISHING_EMAIL_RAW.encode(), "message/rfc822")}
        response = client.post("/analysis/email/file", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 100
    assert data["headers"]["spf_result"] == "fail"


def test_analizar_email_legitimo_da_score_bajo(client, old_whois):
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois):
        files = {"file": ("legit.eml", LEGIT_EMAIL_RAW.encode(), "message/rfc822")}
        response = client.post("/analysis/email/file", files=files)

    assert response.json()["risk_score"] == 0


def test_raw_email_con_saltos_de_linea_reales_no_es_json_valido():
    """
    Documenta el motivo de que exista /analysis/email/file: pegar un email
    raw tal cual dentro de comillas JSON, sin escapar los saltos de línea,
    produce un JSON inválido. Por eso el endpoint de archivo es el
    recomendado para uso manual (ver README).
    """
    import json as json_lib
    broken_body = '{"raw_email": "' + PHISHING_EMAIL_RAW.replace('"', '\\"') + '"}'
    assert "\n" in PHISHING_EMAIL_RAW
    try:
        json_lib.loads(broken_body)
        assert False, "se esperaba que este JSON fuese inválido"
    except json_lib.JSONDecodeError:
        pass  # comportamiento esperado


def test_listado_de_casos_de_email(client, fresh_whois):
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=fresh_whois):
        files = {"file": ("phishing.eml", PHISHING_EMAIL_RAW.encode(), "message/rfc822")}
        client.post("/analysis/email/file", files=files)

    response = client.get("/email-cases")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_pegar_texto_visible_sin_cabeceras_activa_modo_degradado(client):
    """La víctima no siempre puede conseguir el código fuente: pegar solo el
    texto visible debe seguir dando un análisis (aunque limitado), nunca un error."""
    response = client.post("/analysis/email", json={"raw_email": PLAIN_TEXT_PASTE})
    assert response.status_code == 200
    data = response.json()
    assert data["is_raw_source"] is False
    assert "LIMITED_ANALYSIS_NO_RAW_SOURCE" in [f["code"] for f in data["risk_flags"]]


def test_email_con_raw_source_marca_is_raw_source_true(client, old_whois):
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois):
        response = client.post("/analysis/email", json={"raw_email": LEGIT_EMAIL_RAW})
    assert response.json()["is_raw_source"] is True


def test_adjunto_peligroso_se_detecta_a_traves_del_endpoint_de_archivo(client, old_whois):
    msg = MIMEMultipart()
    msg["From"] = "Envios <no-reply@paqueteria-legitima.com>"
    msg["Subject"] = "Tu paquete"
    msg.attach(MIMEText("Cuerpo del mensaje.", "plain"))
    part = MIMEApplication(b"contenido", Name="factura.exe")
    part["Content-Disposition"] = 'attachment; filename="factura.exe"'
    msg.attach(part)

    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois):
        files = {"file": ("con_adjunto.eml", msg.as_string().encode(), "message/rfc822")}
        response = client.post("/analysis/email/file", files=files)

    data = response.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["is_dangerous_extension"] is True
    assert "DANGEROUS_ATTACHMENT" in [f["code"] for f in data["risk_flags"]]


def test_ip_de_origen_con_reputacion_mala_dispara_senal(client, old_whois):
    """La IP del último 'Received' (198.51.100.10 en LEGIT_EMAIL_RAW) se
    enriquece con AbuseIPDB igual que la IP resuelta en el módulo de
    dominio (misma fuente de verdad: ip_risk_engine.evaluate_ip_risk)."""
    abuse_resp = MagicMock()
    abuse_resp.json.return_value = {
        "data": {"ipAddress": "198.51.100.10", "abuseConfidenceScore": 95, "totalReports": 80, "isTor": False}
    }
    abuse_resp.raise_for_status.return_value = None

    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=abuse_resp):
        response = client.post("/analysis/email", json={"raw_email": LEGIT_EMAIL_RAW})

    data = response.json()
    assert data["headers"]["originating_ip"] == "198.51.100.10"
    assert data["originating_ip_abuseipdb"]["abuse_confidence_score"] == 95
    assert "IP_HIGH_ABUSE_SCORE" in [f["code"] for f in data["risk_flags"]]


def test_fallo_de_abuseipdb_para_ip_de_origen_no_tumba_la_respuesta(client, old_whois):
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.abuseipdb_service.requests.get", side_effect=Exception("timeout")), \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"):
        response = client.post("/analysis/email", json={"raw_email": LEGIT_EMAIL_RAW})

    data = response.json()
    assert response.status_code == 200
    assert data["originating_ip_abuseipdb"] is None
    assert any("AbuseIPDB" in e for e in data["errors"])


def test_enlace_del_cuerpo_se_analiza_a_traves_del_endpoint(client, old_whois):
    msg = MIMEMultipart("alternative")
    msg["From"] = "Notificaciones <no-reply@empresa-legitima.com>"
    msg["Subject"] = "Verifica tu cuenta"
    msg.attach(MIMEText(
        '<a href="https://bbva-verificacion-urgente.xyz/login">Verificar</a>', "html",
    ))

    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.email_link_analysis.whois_service.get_whois_info", side_effect=Exception()), \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", side_effect=Exception()):
        files = {"file": ("con_enlace.eml", msg.as_string().encode(), "message/rfc822")}
        response = client.post("/analysis/email/file", files=files)

    data = response.json()
    assert len(data["links"]) == 1
    assert data["links"][0]["suspected_brand"] == "bbva"
    assert "LINK_BRAND_IMPERSONATION" in [f["code"] for f in data["risk_flags"]]
