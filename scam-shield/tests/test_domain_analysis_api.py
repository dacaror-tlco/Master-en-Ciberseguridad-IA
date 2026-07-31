"""
Tests de integración: pasan por la API real (TestClient), con las
llamadas a servicios externos (WHOIS, SSL, VirusTotal) mockeadas. Esto
comprueba que las piezas encajan entre sí (schema -> servicio -> motor de
riesgo -> persistencia -> respuesta), no solo que cada pieza funciona por
separado.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.schemas.domain_analysis import CrtShInfo, DnsRecords, WaybackInfo


def test_analizar_dominio_lo_persiste_y_devuelve_score(client, fresh_whois, fresh_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        response = client.post("/analysis/domain", json={"domain": "banco-falso.xyz"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["domain"] == "banco-falso.xyz"
    assert data["risk_score"] > 0
    assert "DOMAIN_VERY_NEW" in [f["code"] for f in data["risk_flags"]]


def test_dominio_se_normaliza_quitando_protocolo_y_www(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        response = client.post("/analysis/domain", json={"domain": "https://www.ejemplo.com/"})

    assert response.json()["domain"] == "ejemplo.com"


def test_fallo_de_whois_no_tumba_la_respuesta(client, fresh_ssl):
    with patch("app.services.whois_service.get_whois_info", side_effect=Exception("timeout")), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        response = client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["whois"] is None
    assert any("WHOIS falló" in e for e in data["errors"])


def test_analizar_dominio_con_virustotal_configurado(client, old_whois, old_ssl, flagged_vt):
    vt_response = MagicMock()
    vt_response.json.return_value = {"data": {"attributes": {
        "last_analysis_stats": {"malicious": 8, "suspicious": 2, "harmless": 60, "undetected": 10},
        "categories": {"Sophos": "phishing"},
    }}}
    vt_response.raise_for_status.return_value = None

    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.core.config.settings.virustotal_api_key", "fake-key"), \
         patch("app.services.virustotal_service.requests.get", return_value=vt_response):
        response = client.post("/analysis/domain", json={"domain": "banco-falso.xyz"})

    data = response.json()
    assert data["virustotal"]["malicious_count"] == 8
    assert "VT_HIGH_DETECTION" in [f["code"] for f in data["risk_flags"]]


def test_sin_resolucion_dns_ni_abuseipdb_degrada_con_gracia(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.dns_service.get_dns_records", side_effect=Exception("NXDOMAIN")):
        response = client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    data = response.json()
    assert data["resolved_ip"] is None
    assert data["abuseipdb"] is None
    assert data["dns"] is None
    assert any("resolver el dominio" in e for e in data["errors"])


def test_ip_resuelta_con_reputacion_mala_dispara_senal(client, old_whois, old_ssl):
    abuse_resp = MagicMock()
    abuse_resp.json.return_value = {
        "data": {"ipAddress": "5.6.7.8", "abuseConfidenceScore": 95, "totalReports": 80, "isTor": False}
    }
    abuse_resp.raise_for_status.return_value = None

    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.dns_service.get_dns_records", return_value=DnsRecords(all_ips=["5.6.7.8"])), \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=abuse_resp):
        response = client.post("/analysis/domain", json={"domain": "banco-falso.xyz"})

    data = response.json()
    assert data["resolved_ip"] == "5.6.7.8"
    assert data["abuseipdb"]["abuse_confidence_score"] == 95
    assert "IP_HIGH_ABUSE_SCORE" in [f["code"] for f in data["risk_flags"]]
    assert data["ip_reputations"] == [{"ip": "5.6.7.8", "abuseipdb": data["abuseipdb"]}]


def test_varias_ips_resueltas_consultan_reputacion_de_cada_una(client, old_whois, old_ssl):
    """Un dominio con 2 IPs (balanceo/CDN): la principal limpia, la segunda con mala reputación."""
    def fake_abuse(ip):
        from app.schemas.domain_analysis import AbuseIpInfo
        if ip == "9.9.9.9":
            return AbuseIpInfo(ip_address=ip, abuse_confidence_score=95, total_reports=40)
        return AbuseIpInfo(ip_address=ip, abuse_confidence_score=0)

    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.dns_service.get_dns_records", return_value=DnsRecords(all_ips=["1.1.1.1", "9.9.9.9"])), \
         patch("app.services.abuseipdb_service.get_ip_reputation", side_effect=fake_abuse):
        response = client.post("/analysis/domain", json={"domain": "multi-ip.com"})

    data = response.json()
    assert data["resolved_ip"] == "1.1.1.1"
    assert data["abuseipdb"]["abuse_confidence_score"] == 0
    assert len(data["ip_reputations"]) == 2
    assert "ADDITIONAL_IP_HIGH_ABUSE_SCORE" in [f["code"] for f in data["risk_flags"]]


def test_dominio_sin_spf_ni_dmarc_se_refleja_en_dns_y_senales(client, old_whois, old_ssl):
    dns_info = DnsRecords(all_ips=["1.2.3.4"], mx_hosts=["mx.dominio-sospechoso.com"], has_spf=False, has_dmarc=False)
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.dns_service.get_dns_records", return_value=dns_info):
        response = client.post("/analysis/domain", json={"domain": "dominio-sospechoso.com"})

    data = response.json()
    assert data["dns"]["mx_hosts"] == ["mx.dominio-sospechoso.com"]
    assert data["dns"]["has_spf"] is False
    codes = [f["code"] for f in data["risk_flags"]]
    assert "DOMAIN_NO_SPF" in codes
    assert "DOMAIN_NO_DMARC" in codes


def test_crtsh_con_subdominio_de_marca_dispara_senal(client, old_whois, old_ssl):
    crtsh_info = CrtShInfo(
        subdomain_count=1, subdomains=["bbva-secure.dominio-malo.xyz"],
        suspected_brand_subdomains=["bbva-secure.dominio-malo.xyz"],
    )
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.crtsh_service.get_crtsh_info", return_value=crtsh_info):
        response = client.post("/analysis/domain", json={"domain": "dominio-malo.xyz"})

    data = response.json()
    assert data["crtsh"]["subdomain_count"] == 1
    assert "SUBDOMAIN_BRAND_IMPERSONATION" in [f["code"] for f in data["risk_flags"]]


def test_crtsh_caido_no_tumba_el_analisis(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.crtsh_service.get_crtsh_info", side_effect=Exception("502 Bad Gateway")):
        response = client.post("/analysis/domain", json={"domain": "ejemplo.com"})

    data = response.json()
    assert response.status_code == 200
    assert data["crtsh"] is None
    assert any("crt.sh" in e for e in data["errors"])


def test_wayback_dominio_reciclado_dispara_senal(client, fresh_whois, old_ssl):
    wayback_info = WaybackInfo(
        total_snapshots=20,
        first_snapshot=datetime(2010, 1, 1, tzinfo=timezone.utc),
        last_snapshot=datetime(2012, 1, 1, tzinfo=timezone.utc),
    )
    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl), \
         patch("app.services.wayback_service.get_wayback_info", return_value=wayback_info):
        response = client.post("/analysis/domain", json={"domain": "reciclado.com"})

    data = response.json()
    assert data["wayback"]["total_snapshots"] == 20
    assert "DOMAIN_REUSED_AFTER_EXPIRY" in [f["code"] for f in data["risk_flags"]]


def test_listado_de_casos_devuelve_los_creados(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        client.post("/analysis/domain", json={"domain": "uno.com"})
        client.post("/analysis/domain", json={"domain": "dos.com"})

    response = client.get("/cases")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_obtener_caso_inexistente_da_404(client):
    response = client.get("/cases/9999")
    assert response.status_code == 404
