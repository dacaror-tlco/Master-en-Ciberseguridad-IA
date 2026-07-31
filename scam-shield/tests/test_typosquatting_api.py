from unittest.mock import MagicMock, patch


def _fake_abuseipdb_response(score):
    resp = MagicMock()
    resp.json.return_value = {"data": {"ipAddress": "1.2.3.4", "abuseConfidenceScore": score, "totalReports": 10}}
    resp.raise_for_status.return_value = None
    return resp


def test_typosquatting_basico_sin_analisis_profundo(client):
    fake_dns = {"acebook.com": "1.2.3.4", "facebok.com": "5.6.7.8"}

    with patch("app.services.dns_service.check_dns_bulk") as mock_dns:
        # Simulamos que solo 2 de todas las variantes generadas resuelven
        def side_effect(domains, **kwargs):
            return {d: fake_dns.get(d) for d in domains}
        mock_dns.side_effect = side_effect

        response = client.post("/analysis/typosquatting", json={"domain": "facebook.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["resolved_count"] == 2
    assert data["risk_score"] > 0
    variants_found = {c["variant"] for c in data["candidates"]}
    assert variants_found == {"acebook.com", "facebok.com"}
    # sin include_full_analysis, no se llama a WHOIS/SSL/VT -> risk_score de cada candidato es None
    assert all(c["risk_score"] is None for c in data["candidates"])


def test_typosquatting_con_analisis_profundo(client, fresh_whois, fresh_ssl):
    with patch("app.services.dns_service.check_dns_bulk") as mock_dns, \
         patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl), \
         patch("app.services.virustotal_service.get_virustotal_info", side_effect=Exception("sin key")):
        mock_dns.side_effect = lambda domains, **kwargs: {"acebook.com": "1.2.3.4", **{d: None for d in domains if d != "acebook.com"}}

        response = client.post("/analysis/typosquatting", json={
            "domain": "facebook.com", "include_full_analysis": True, "max_full_analysis": 3,
        })

    data = response.json()
    analyzed = [c for c in data["candidates"] if c["variant"] == "acebook.com"][0]
    assert analyzed["risk_score"] is not None
    assert analyzed["risk_score"] > 0  # fresh_whois/fresh_ssl son señales de riesgo


def test_typosquatting_sin_variantes_activas_da_score_cero(client):
    with patch("app.services.dns_service.check_dns_bulk", return_value={}):
        response = client.post("/analysis/typosquatting", json={"domain": "marca-super-protegida.com"})

    data = response.json()
    assert data["resolved_count"] == 0
    assert data["risk_score"] == 0


def test_variantes_activas_reciben_reputacion_de_ip_sin_analisis_profundo(client):
    """La reputación de IP (AbuseIPDB) se aplica a TODAS las variantes activas, incluso sin include_full_analysis."""
    with patch("app.services.dns_service.check_dns_bulk") as mock_dns, \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=_fake_abuseipdb_response(90)):
        mock_dns.side_effect = lambda domains, **kwargs: {"acebook.com": "1.2.3.4", **{d: None for d in domains if d != "acebook.com"}}
        response = client.post("/analysis/typosquatting", json={"domain": "facebook.com"})

    data = response.json()
    candidate = data["candidates"][0]
    assert candidate["abuseipdb"]["abuse_confidence_score"] == 90
    assert candidate["risk_score"] == 40  # IP_HIGH_ABUSE_SCORE
    assert candidate["fully_analyzed"] is False
    assert "TYPOSQUATTING_VARIANT_ON_ABUSIVE_IP" not in [f["code"] for f in data["risk_flags"]]  # score 40 < 60


def test_variantes_que_comparten_ip_solo_consultan_una_vez(client):
    with patch("app.services.dns_service.check_dns_bulk") as mock_dns, \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=_fake_abuseipdb_response(20)) as mock_get:
        # Dos variantes distintas, misma IP -> mismo hosting, típico de campañas grandes
        mock_dns.side_effect = lambda domains, **kwargs: {
            "acebook.com": "1.2.3.4", "facebok.com": "1.2.3.4",
            **{d: None for d in domains if d not in ("acebook.com", "facebok.com")},
        }
        response = client.post("/analysis/typosquatting", json={"domain": "facebook.com"})

    assert response.json()["resolved_count"] == 2
    assert mock_get.call_count == 1


def test_sin_abuseipdb_key_degrada_con_gracia_en_typosquatting(client):
    with patch("app.services.dns_service.check_dns_bulk") as mock_dns:
        mock_dns.side_effect = lambda domains, **kwargs: {"acebook.com": "1.2.3.4", **{d: None for d in domains if d != "acebook.com"}}
        response = client.post("/analysis/typosquatting", json={"domain": "facebook.com"})

    data = response.json()
    assert data["candidates"][0]["risk_score"] is None
    assert any("AbuseIPDB" in e for e in data["errors"])


def test_respeta_el_tope_max_ip_checks(client):
    fake_variants = [(f"variant{i}.com", "omission") for i in range(5)]
    fake_ips = {f"variant{i}.com": f"9.9.9.{i}" for i in range(5)}  # 5 IPs distintas, sin compartir hosting

    with patch("app.services.typosquatting_service.generate_variants", return_value=fake_variants), \
         patch("app.services.dns_service.check_dns_bulk", return_value=fake_ips), \
         patch("app.core.config.settings.abuseipdb_api_key", "fake-key"), \
         patch("app.services.abuseipdb_service.requests.get", return_value=_fake_abuseipdb_response(10)) as mock_get:
        response = client.post("/analysis/typosquatting", json={"domain": "facebook.com", "max_ip_checks": 2})

    assert response.status_code == 200
    assert mock_get.call_count == 2
    scored = [c for c in response.json()["candidates"] if c["risk_score"] is not None]
    assert len(scored) == 2


def test_dominio_sin_formato_valido_da_400(client):
    response = client.post("/analysis/typosquatting", json={"domain": "sindominiovalido"})
    assert response.status_code == 400


def test_listado_de_casos_typosquatting(client):
    with patch("app.services.dns_service.check_dns_bulk", return_value={}):
        client.post("/analysis/typosquatting", json={"domain": "marca.com"})

    response = client.get("/typosquatting-cases")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_obtener_caso_typosquatting_inexistente_da_404(client):
    response = client.get("/typosquatting-cases/9999")
    assert response.status_code == 404
