"""
Tests de enriquecimiento de enlaces. Mockeamos whois_service/virustotal_service
y la resolución de acortadores (requests.head) para no hacer llamadas de red
reales, siguiendo el mismo criterio que el resto de la suite (ver conftest.py).
"""
from unittest.mock import patch

from app.schemas.domain_analysis import VirusTotalInfo, WhoisInfo
from app.services.email_link_analysis import analyze_links


def test_dominio_de_confianza_no_se_consulta(fresh_whois):
    with patch("app.services.email_link_analysis.whois_service.get_whois_info") as mock_whois:
        results = analyze_links(["https://www.google.com/search?q=algo"])
    mock_whois.assert_not_called()
    assert results[0].checked is False


def test_dominio_desconocido_se_consulta_whois_y_virustotal(fresh_whois):
    vt_info = VirusTotalInfo(malicious_count=3, suspicious_count=0, harmless_count=10, undetected_count=1)
    with patch("app.services.email_link_analysis.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", return_value=vt_info):
        results = analyze_links(["https://banco-falso-verificacion.xyz/login"])
    assert results[0].checked is True
    assert results[0].domain_age_days == fresh_whois.domain_age_days
    assert results[0].virustotal_malicious_count == 3


def test_acortador_resuelve_destino_y_no_se_marca_dos_veces():
    with patch("app.services.email_link_analysis._resolve_shortener", return_value="destino-real.com"), \
         patch("app.services.email_link_analysis.whois_service.get_whois_info", side_effect=Exception("no importa")), \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", side_effect=Exception("no importa")):
        results = analyze_links(["https://bit.ly/abc123"])
    assert results[0].is_shortener is True
    assert results[0].redirects_to == "destino-real.com"


def test_dominio_que_imita_marca_conocida_se_marca_como_sospechoso():
    with patch("app.services.email_link_analysis.whois_service.get_whois_info", side_effect=Exception()), \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", side_effect=Exception()):
        results = analyze_links(["https://bbva-verificacion-urgente.xyz/login"])
    assert results[0].suspected_brand == "bbva"


def test_dominio_oficial_de_la_marca_no_se_marca_como_sospechoso():
    with patch("app.services.email_link_analysis.whois_service.get_whois_info", side_effect=Exception()), \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", side_effect=Exception()):
        results = analyze_links(["https://bbva.es/area-clientes"])
    assert results[0].suspected_brand is None


def test_maximo_de_dominios_consultados_se_respeta():
    urls = [f"https://dominio-distinto-{i}.xyz/pagina" for i in range(8)]
    with patch("app.services.email_link_analysis.whois_service.get_whois_info", side_effect=Exception()) as mock_whois, \
         patch("app.services.email_link_analysis.virustotal_service.get_virustotal_info", side_effect=Exception()):
        results = analyze_links(urls)
    assert len(results) == 8
    assert mock_whois.call_count == 5  # _MAX_DOMAINS_CHECKED
    assert sum(1 for r in results if r.checked) == 5
