from app.schemas.domain_analysis import WhoisInfo
from app.schemas.email_analysis import EmailAttachmentInfo, EmailHeaderInfo, EmailLinkInfo
from app.services.email_risk_engine import evaluate_email_risk
from app.services.email_service import parse_email_headers
from tests.conftest import LEGIT_EMAIL_RAW, PHISHING_EMAIL_RAW


def test_email_legitimo_da_score_cero():
    headers = parse_email_headers(LEGIT_EMAIL_RAW)
    old_whois = WhoisInfo(domain_age_days=3000, registrar="Legit Inc")
    flags, score = evaluate_email_risk(headers, old_whois)
    assert score == 0
    assert flags == []


def test_email_phishing_dispara_las_senales_esperadas(fresh_whois):
    headers = parse_email_headers(PHISHING_EMAIL_RAW)
    flags, score = evaluate_email_risk(headers, fresh_whois)
    codes = {f.code for f in flags}
    assert {"SPF_FAIL", "DKIM_FAIL", "DMARC_FAIL", "REPLY_TO_MISMATCH", "SUSPICIOUS_TLD", "SENDER_DOMAIN_VERY_NEW"} <= codes
    assert score == 100


def test_parseo_extrae_ip_de_origen_del_received():
    headers = parse_email_headers(PHISHING_EMAIL_RAW)
    assert headers.originating_ip == "203.0.113.55"


def test_parseo_extrae_remitente_y_asunto():
    headers = parse_email_headers(PHISHING_EMAIL_RAW)
    assert headers.from_address == "soporte@banco-seguro-verificacion.xyz"
    assert headers.subject == "Tu cuenta ha sido bloqueada"


def test_sin_reply_to_no_dispara_mismatch():
    headers = parse_email_headers(LEGIT_EMAIL_RAW)
    assert headers.reply_to is None
    flags, _ = evaluate_email_risk(headers, None)
    assert "REPLY_TO_MISMATCH" not in [f.code for f in flags]


def test_spf_pass_no_anade_penalizacion():
    headers = parse_email_headers(LEGIT_EMAIL_RAW)
    flags, _ = evaluate_email_risk(headers, None)
    assert "SPF_FAIL" not in [f.code for f in flags]
    assert "SPF_MISSING" not in [f.code for f in flags]


def test_nombre_visible_suplanta_marca_sin_ser_su_dominio():
    headers = EmailHeaderInfo(from_address="soporte@gmail.com", from_display_name="Banco Santander")
    flags, score = evaluate_email_risk(headers, None)
    assert "DISPLAY_NAME_BRAND_MISMATCH" in [f.code for f in flags]
    assert score >= 35


def test_nombre_visible_con_marca_y_dominio_oficial_no_dispara_nada():
    headers = EmailHeaderInfo(from_address="notificaciones@santander.com", from_display_name="Banco Santander")
    flags, score = evaluate_email_risk(headers, None)
    assert "DISPLAY_NAME_BRAND_MISMATCH" not in [f.code for f in flags]


def test_enlace_acortado_dispara_shortened_link():
    headers = EmailHeaderInfo()
    links = [EmailLinkInfo(url="https://bit.ly/abc", domain="bit.ly", is_shortener=True)]
    flags, score = evaluate_email_risk(headers, None, links=links)
    assert "SHORTENED_LINK" in [f.code for f in flags]


def test_enlace_que_imita_marca_dispara_link_brand_impersonation():
    headers = EmailHeaderInfo()
    links = [EmailLinkInfo(url="https://bbva-verificacion.xyz/login", domain="bbva-verificacion.xyz", suspected_brand="bbva")]
    flags, score = evaluate_email_risk(headers, None, links=links)
    assert "LINK_BRAND_IMPERSONATION" in [f.code for f in flags]


def test_enlace_a_dominio_muy_nuevo_dispara_flag():
    headers = EmailHeaderInfo()
    links = [EmailLinkInfo(url="https://algo-raro.xyz", domain="algo-raro.xyz", domain_age_days=2)]
    flags, _ = evaluate_email_risk(headers, None, links=links)
    assert "LINK_DOMAIN_VERY_NEW" in [f.code for f in flags]


def test_enlace_marcado_por_virustotal_dispara_flag():
    headers = EmailHeaderInfo()
    links = [EmailLinkInfo(url="https://malo.com", domain="malo.com", virustotal_malicious_count=5)]
    flags, _ = evaluate_email_risk(headers, None, links=links)
    assert "LINK_FLAGGED_BY_VIRUSTOTAL" in [f.code for f in flags]


def test_adjunto_con_extension_peligrosa_dispara_flag():
    headers = EmailHeaderInfo()
    attachments = [EmailAttachmentInfo(filename="factura.exe", extension="exe", size_bytes=100, sha256="a" * 64, is_dangerous_extension=True)]
    flags, score = evaluate_email_risk(headers, None, attachments=attachments)
    assert "DANGEROUS_ATTACHMENT" in [f.code for f in flags]
    assert score >= 35


def test_adjunto_con_doble_extension_dispara_flag():
    headers = EmailHeaderInfo()
    attachments = [EmailAttachmentInfo(filename="factura.pdf.exe", extension="exe", size_bytes=100, sha256="a" * 64, has_double_extension=True)]
    flags, _ = evaluate_email_risk(headers, None, attachments=attachments)
    assert "DOUBLE_EXTENSION_ATTACHMENT" in [f.code for f in flags]


def test_adjunto_normal_no_dispara_nada():
    headers = EmailHeaderInfo()
    attachments = [EmailAttachmentInfo(filename="factura.pdf", extension="pdf", size_bytes=100, sha256="a" * 64)]
    flags, _ = evaluate_email_risk(headers, None, attachments=attachments, is_raw_source=False)
    codes = [f.code for f in flags]
    assert "DANGEROUS_ATTACHMENT" not in codes
    assert "DOUBLE_EXTENSION_ATTACHMENT" not in codes


def test_modo_degradado_sin_raw_source_no_dispara_flags_de_cabeceras_ausentes():
    """Sin código fuente real no hay SPF/DKIM que comprobar: no debe salir SPF_MISSING/DKIM_MISSING,
    sino un único flag informativo de análisis limitado."""
    headers = EmailHeaderInfo()
    flags, score = evaluate_email_risk(headers, None, is_raw_source=False)
    codes = [f.code for f in flags]
    assert codes == ["LIMITED_ANALYSIS_NO_RAW_SOURCE"]
    assert score == 0


def test_modo_degradado_sigue_detectando_suplantacion_de_marca():
    headers = EmailHeaderInfo(from_address="alguien@gmail.com", from_display_name="Correos")
    flags, _ = evaluate_email_risk(headers, None, is_raw_source=False)
    codes = [f.code for f in flags]
    assert "LIMITED_ANALYSIS_NO_RAW_SOURCE" in codes
    assert "DISPLAY_NAME_BRAND_MISMATCH" in codes
