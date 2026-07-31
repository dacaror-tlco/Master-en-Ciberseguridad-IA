"""
Tests unitarios de risk_engine.py (dominio).

Al ser lógica pura (sin red, sin base de datos), estos tests son rápidos
y deterministas — son los más valiosos para detectar regresiones cuando
se toquen los umbrales o se añadan nuevas señales.
"""
from datetime import datetime, timedelta, timezone

from app.schemas.domain_analysis import AbuseIpInfo, CrtShInfo, DnsRecords, IpReputationEntry, SSLCertInfo, VirusTotalInfo, WaybackInfo, WhoisInfo
from app.services.risk_engine import evaluate_risk


def test_dominio_limpio_da_score_cero(old_whois, old_ssl):
    flags, score = evaluate_risk(old_whois, old_ssl)
    assert score == 0
    assert flags == []


def test_dominio_recien_registrado_dispara_domain_very_new(fresh_whois, old_ssl):
    flags, score = evaluate_risk(fresh_whois, old_ssl)
    codes = [f.code for f in flags]
    assert "DOMAIN_VERY_NEW" in codes
    assert score > 0


def test_dominio_moderadamente_reciente_da_severidad_media():
    whois = WhoisInfo(domain_age_days=90, registrar="Algún Registrar")
    flags, _ = evaluate_risk(whois, None)
    domain_recent = next(f for f in flags if f.code == "DOMAIN_RECENT")
    assert domain_recent.severity == "medium"


def test_sin_registrador_dispara_whois_hidden():
    whois = WhoisInfo(domain_age_days=1000, registrar=None)
    flags, _ = evaluate_risk(whois, None)
    assert "WHOIS_HIDDEN" in [f.code for f in flags]


def test_certificado_invalido_dispara_no_valid_ssl():
    ssl_info = SSLCertInfo(has_valid_cert=False)
    flags, score = evaluate_risk(None, ssl_info)
    assert "NO_VALID_SSL" in [f.code for f in flags]
    assert score >= 30


def test_certificado_recien_emitido_dispara_cert_just_issued(fresh_ssl):
    flags, _ = evaluate_risk(None, fresh_ssl)
    assert "CERT_JUST_ISSUED" in [f.code for f in flags]


def test_virustotal_limpio_no_anade_senales(clean_vt):
    flags, score = evaluate_risk(None, None, clean_vt)
    assert flags == []
    assert score == 0


def test_virustotal_alta_deteccion_dispara_vt_high_detection(flagged_vt):
    flags, score = evaluate_risk(None, None, flagged_vt)
    codes = [f.code for f in flags]
    assert "VT_HIGH_DETECTION" in codes
    assert "VT_SUSPICIOUS_VOTES" in codes
    assert score >= 40


def test_virustotal_una_sola_deteccion_es_severidad_media():
    vt = VirusTotalInfo(malicious_count=1)
    flags, _ = evaluate_risk(None, None, vt)
    detection_flag = next(f for f in flags if f.code == "VT_SOME_DETECTION")
    assert detection_flag.severity == "medium"


def test_caso_de_phishing_realista_combina_todas_las_senales(fresh_whois, fresh_ssl, flagged_vt):
    flags, score = evaluate_risk(fresh_whois, fresh_ssl, flagged_vt)
    codes = {f.code for f in flags}
    assert {"DOMAIN_VERY_NEW", "WHOIS_HIDDEN", "CERT_JUST_ISSUED", "VT_HIGH_DETECTION", "VT_SUSPICIOUS_VOTES"} <= codes
    assert score == 100  # el score se satura en 100 aunque la suma de pesos lo supere


def test_score_nunca_supera_100(fresh_whois, fresh_ssl, flagged_vt):
    _, score = evaluate_risk(fresh_whois, fresh_ssl, flagged_vt)
    assert score <= 100


def test_sin_abuseipdb_info_no_anade_senal():
    flags, score = evaluate_risk(None, None, None, None)
    assert flags == []
    assert score == 0


def test_ip_con_reputacion_mala_se_combina_con_el_resto(fresh_whois, fresh_ssl):
    abuseipdb_info = AbuseIpInfo(ip_address="1.2.3.4", abuse_confidence_score=90, total_reports=50)
    flags, score = evaluate_risk(fresh_whois, fresh_ssl, None, abuseipdb_info)
    codes = {f.code for f in flags}
    assert {"DOMAIN_VERY_NEW", "IP_HIGH_ABUSE_SCORE"} <= codes
    assert score <= 100


def test_sin_mx_no_evalua_spf_dmarc():
    """Un dominio sin MX no recibe correo: no tiene sentido pedirle SPF/DMARC."""
    dns_info = DnsRecords(all_ips=["1.2.3.4"], mx_hosts=[], has_spf=False, has_dmarc=False)
    flags, score = evaluate_risk(None, None, dns_info=dns_info)
    assert flags == []
    assert score == 0


def test_con_mx_sin_spf_ni_dmarc_dispara_ambas_senales():
    dns_info = DnsRecords(all_ips=["1.2.3.4"], mx_hosts=["mx.ejemplo.com"], has_spf=False, has_dmarc=False)
    flags, score = evaluate_risk(None, None, dns_info=dns_info)
    codes = {f.code for f in flags}
    assert {"DOMAIN_NO_SPF", "DOMAIN_NO_DMARC"} <= codes
    assert score > 0


def test_con_mx_y_spf_dmarc_configurados_no_dispara_nada():
    dns_info = DnsRecords(all_ips=["1.2.3.4"], mx_hosts=["mx.ejemplo.com"], has_spf=True, has_dmarc=True)
    flags, score = evaluate_risk(None, None, dns_info=dns_info)
    assert flags == []
    assert score == 0


def test_ip_adicional_con_mala_reputacion_dispara_senal_prefijada():
    """La IP principal (5.6.7.8) no tiene reputación mala; la IP EXTRA (9.9.9.9) sí."""
    primary = IpReputationEntry(ip="5.6.7.8", abuseipdb=AbuseIpInfo(ip_address="5.6.7.8", abuse_confidence_score=0))
    extra = IpReputationEntry(ip="9.9.9.9", abuseipdb=AbuseIpInfo(ip_address="9.9.9.9", abuse_confidence_score=95, total_reports=50))
    flags, score = evaluate_risk(None, None, ip_reputations=[primary, extra], resolved_ip="5.6.7.8")
    codes = [f.code for f in flags]
    assert "ADDITIONAL_IP_HIGH_ABUSE_SCORE" in codes
    assert "IP_HIGH_ABUSE_SCORE" not in codes  # ese código es solo para la IP principal (parámetro abuseipdb_info)
    assert "9.9.9.9" in next(f for f in flags if f.code == "ADDITIONAL_IP_HIGH_ABUSE_SCORE").description
    assert score > 0


def test_subdominio_con_marca_suplantada_dispara_senal():
    crtsh_info = CrtShInfo(subdomain_count=1, subdomains=["bbva-verificacion.ejemplo.xyz"], suspected_brand_subdomains=["bbva-verificacion.ejemplo.xyz"])
    flags, score = evaluate_risk(None, None, crtsh_info=crtsh_info)
    assert "SUBDOMAIN_BRAND_IMPERSONATION" in [f.code for f in flags]
    assert score > 0


def test_crtsh_sin_marcas_sospechosas_no_dispara_nada():
    crtsh_info = CrtShInfo(subdomain_count=3, subdomains=["www.ejemplo.com", "api.ejemplo.com", "mail.ejemplo.com"])
    flags, score = evaluate_risk(None, None, crtsh_info=crtsh_info)
    assert flags == []
    assert score == 0


def test_dominio_nunca_archivado_dispara_senal_baja():
    wayback_info = WaybackInfo(total_snapshots=0)
    flags, score = evaluate_risk(None, None, wayback_info=wayback_info)
    flag = next(f for f in flags if f.code == "DOMAIN_NEVER_ARCHIVED")
    assert flag.severity == "low"
    assert score == 5


def test_dominio_reutilizado_tras_expirar_dispara_senal_alta():
    """Wayback tiene una captura de 2015, pero el WHOIS dice que se registró hace poco: dominio expirado y reciclado."""
    whois = WhoisInfo(domain_age_days=10, creation_date=datetime.now(timezone.utc) - timedelta(days=10))
    wayback_info = WaybackInfo(
        total_snapshots=50,
        first_snapshot=datetime(2015, 1, 1, tzinfo=timezone.utc),
        last_snapshot=datetime(2016, 1, 1, tzinfo=timezone.utc),
    )
    flags, score = evaluate_risk(whois, None, wayback_info=wayback_info)
    assert "DOMAIN_REUSED_AFTER_EXPIRY" in [f.code for f in flags]
    assert score >= 35


def test_wayback_snapshot_reciente_coherente_con_whois_no_dispara_reuso():
    """El primer snapshot es POSTERIOR al registro (caso normal: se indexó tras crearse), no debe leerse como reciclado."""
    now = datetime.now(timezone.utc)
    whois = WhoisInfo(domain_age_days=100, creation_date=now - timedelta(days=100))
    wayback_info = WaybackInfo(total_snapshots=5, first_snapshot=now - timedelta(days=90), last_snapshot=now - timedelta(days=1))
    flags, _ = evaluate_risk(whois, None, wayback_info=wayback_info)
    assert "DOMAIN_REUSED_AFTER_EXPIRY" not in [f.code for f in flags]
