from unittest.mock import MagicMock, patch


def _create_domain_and_email_case(client, fresh_whois, fresh_ssl):
    """Helper: crea un dominio y un email del mismo remitente (para que correlacionen)."""
    from tests.conftest import PHISHING_EMAIL_RAW

    with patch("app.services.whois_service.get_whois_info", return_value=fresh_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=fresh_ssl):
        domain_id = client.post("/analysis/domain", json={"domain": "banco-seguro-verificacion.xyz"}).json()["id"]

    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=fresh_whois):
        files = {"file": ("p.eml", PHISHING_EMAIL_RAW.encode(), "message/rfc822")}
        email_id = client.post("/analysis/email/file", files=files).json()["id"]

    return domain_id, email_id


# ---------------------------------------------------------------------
# Informe PDF
# ---------------------------------------------------------------------

def test_generar_informe_devuelve_un_pdf_valido(client, fresh_whois, fresh_ssl):
    domain_id, email_id = _create_domain_and_email_case(client, fresh_whois, fresh_ssl)

    response = client.post("/reports/generate", json={"domain_case_ids": [domain_id], "email_case_ids": [email_id]})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"  # firma binaria estándar de un PDF válido


def test_informe_con_caso_de_typosquatting(client):
    with patch("app.services.dns_service.check_dns_bulk", return_value={"acebook.com": "1.2.3.4"}):
        typo_id = client.post("/analysis/typosquatting", json={"domain": "facebook.com"}).json()["id"]

    response = client.post("/reports/generate", json={"typosquatting_case_ids": [typo_id]})

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_informe_con_caso_de_telefono(client):
    phone_id = client.post("/analysis/phone", json={"phone": "+34803123456", "default_region": "ES"}).json()["id"]

    response = client.post("/reports/generate", json={"phone_case_ids": [phone_id]})

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_informe_con_imagen_y_busqueda_facial(client):
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (50, 50), color=(10, 20, 30)).save(buf, format="JPEG")
    image_id = client.post("/analysis/image", files={"file": ("foto.jpg", buf.getvalue(), "image/jpeg")}).json()["id"]

    client.post(f"/analysis/image/{image_id}/facial-search", data={"confirmed_legal_basis": "true", "notes": "Caso de prueba"})

    response = client.post("/reports/generate", json={"image_case_ids": [image_id]})

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_informe_sin_casos_da_400(client):
    response = client.post("/reports/generate", json={})
    assert response.status_code == 400


def test_informe_con_caso_inexistente_da_404(client):
    response = client.post("/reports/generate", json={"domain_case_ids": [9999]})
    assert response.status_code == 404


# ---------------------------------------------------------------------
# Análisis consolidado (correlación + IA)
# ---------------------------------------------------------------------

def test_consolidado_detecta_correlacion_entre_dominio_y_email(client, fresh_whois, fresh_ssl):
    domain_id, email_id = _create_domain_and_email_case(client, fresh_whois, fresh_ssl)

    response = client.post("/analysis/consolidated", json={
        "domain_case_ids": [domain_id], "email_case_ids": [email_id], "include_ai_narrative": False,
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data["correlation_flags"]) == 1
    assert data["correlation_flags"][0]["code"] == "DOMAIN_MATCHES_EMAIL_SENDER"
    assert data["consolidated_score"] == 100


def test_consolidado_sin_api_key_degrada_con_explicacion(client, fresh_whois, fresh_ssl):
    domain_id, email_id = _create_domain_and_email_case(client, fresh_whois, fresh_ssl)

    with patch("app.core.config.settings.anthropic_api_key", ""):
        response = client.post("/analysis/consolidated", json={
            "domain_case_ids": [domain_id], "email_case_ids": [email_id],
        })

    data = response.json()
    assert data["ai_narrative"] is None
    assert "ANTHROPIC_API_KEY" in data["ai_narrative_error"]


def test_consolidado_con_ia_mockeada_genera_narrativa(client, fresh_whois, fresh_ssl):
    domain_id, email_id = _create_domain_and_email_case(client, fresh_whois, fresh_ssl)

    mock_block = MagicMock(type="text", text="Narrativa de prueba generada por el LLM.")
    mock_response = MagicMock(content=[mock_block])

    with patch("app.core.config.settings.anthropic_api_key", "fake-key"), \
         patch("app.services.ai_service.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_response
        response = client.post("/analysis/consolidated", json={
            "domain_case_ids": [domain_id], "email_case_ids": [email_id],
        })

    assert response.json()["ai_narrative"] == "Narrativa de prueba generada por el LLM."


def test_consolidado_sin_casos_da_400(client):
    response = client.post("/analysis/consolidated", json={})
    assert response.status_code == 400
