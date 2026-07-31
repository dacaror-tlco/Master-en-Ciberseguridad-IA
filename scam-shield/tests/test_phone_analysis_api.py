def test_analizar_movil_normal(client):
    response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})
    assert response.status_code == 200
    data = response.json()
    assert data["phone"]["line_type"] == "MOBILE"
    assert data["risk_score"] == 0
    assert data["risk_flags"] == []


def test_analizar_tarificacion_especial(client):
    response = client.post("/analysis/phone", json={"phone": "+34803123456", "default_region": "ES"})
    data = response.json()
    assert data["risk_score"] == 50
    assert "PHONE_PREMIUM_RATE" in [f["code"] for f in data["risk_flags"]]


def test_analizar_voip(client):
    response = client.post("/analysis/phone", json={"phone": "+445600000000", "default_region": "GB"})
    data = response.json()
    assert "PHONE_VOIP" in [f["code"] for f in data["risk_flags"]]


def test_texto_no_telefonico_da_400(client):
    response = client.post("/analysis/phone", json={"phone": "esto no es un teléfono", "default_region": "ES"})
    assert response.status_code == 400


def test_se_persiste_y_aparece_en_el_listado(client):
    client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})
    client.post("/analysis/phone", json={"phone": "+34803123456", "default_region": "ES"})

    response = client.get("/phone-cases")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_obtener_caso_inexistente_da_404(client):
    response = client.get("/phone-cases/9999")
    assert response.status_code == 404


def test_obtener_caso_concreto(client):
    created = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"}).json()
    response = client.get(f"/phone-cases/{created['id']}")
    assert response.status_code == 200
    assert response.json()["phone"]["e164"] == "+34600123456"


def test_sin_openspam_api_key_degrada_con_gracia(client):
    """Comportamiento por defecto: sin OPENSPAM_API_KEY, el análisis sigue funcionando sin esa señal."""
    response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})
    data = response.json()
    assert response.status_code == 200
    assert data["community_reports"] is None
    assert any("OpenSpam" in e for e in data["errors"])


def test_numero_muy_reportado_dispara_senal_alta(client):
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "data": {"telefono": "+34600123456", "reportes": 47, "tipo": "fraude", "provincia": "Madrid", "nivel_peligro": "alto"},
    }
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})

    data = response.json()
    assert data["community_reports"]["reports_count"] == 47
    assert "PHONE_COMMUNITY_REPORTED_HIGH" in [f["code"] for f in data["risk_flags"]]


def test_numero_no_reportado_no_anade_senal(client):
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True, "data": {"telefono": "+34600123456", "reportes": 0}}
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})

    data = response.json()
    assert data["risk_score"] == 0
    assert data["risk_flags"] == []


def test_numero_no_encontrado_404_da_cero_reportes_no_error(client):
    """
    Regresión: OpenSpam responde 404 cuando el número nunca se ha
    reportado (caso normal, no un fallo). Antes esto se colaba como
    'OpenSpam falló' en errors y community_reports quedaba en null,
    haciendo parecer que la integración no funcionaba en absoluto.
    """
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34699999999", "default_region": "ES"})

    data = response.json()
    assert data["community_reports"] == {"reports_count": 0, "category": None, "province": None, "danger_level": None}
    assert not any("OpenSpam" in e for e in data["errors"])
    assert data["risk_score"] == 0


def test_numero_no_encontrado_success_false_da_cero_reportes_no_error(client):
    """Mismo caso que arriba, pero si la API responde 200 con success=False en vez de un 404 real."""
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"success": False, "message": "Número no encontrado"}
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34699999999", "default_region": "ES"})

    data = response.json()
    assert data["community_reports"]["reports_count"] == 0
    assert not any("OpenSpam" in e for e in data["errors"])


def test_respuesta_con_estructura_plana_fallback(client):
    """
    El código soporta también una estructura plana (data.total_reportes
    directamente) como fallback, por si la API varía entre entornos. No es
    la estructura real observada en producción (ver el test de abajo para
    esa), pero queremos que este caso siga funcionando si aparece.
    """
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {
            "id": 362657, "telefono": "+3901119115987", "total_reportes": 2024,
            "total_consultas": 0, "nivel_peligro": "alto", "bloqueado": 0, "verificado": 0,
            "provincia": None, "operadora": "Fisso", "tipo_spam": "spam",
            "tipo_descripcion": "Llamada publicitaria no solicitada", "tipo_spam_amigable": "Spam",
            "peligro_score": 65, "peligro_nivel": "alto",
        },
    }
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+3901119115987", "default_region": "IT"})

    data = response.json()
    assert data["community_reports"]["reports_count"] == 2024
    assert data["community_reports"]["category"] == "spam"
    assert data["community_reports"]["danger_level"] == "alto"
    assert "PHONE_COMMUNITY_REPORTED_HIGH" in [f["code"] for f in data["risk_flags"]]


def test_respuesta_real_de_produccion_con_estructura_anidada(client):
    """
    Regresión con la respuesta REAL capturada de la demo pública de OpenSpam
    (pegada literal por un usuario, no la documentación). La estructura real
    anida los datos del número bajo data.numero, no directamente en data —
    ni la documentación oficial ni la muestra de /api/top que vimos antes
    dejaban ver esto. Sin este ajuste, CUALQUIER número reportado (incluso
    con 2000+ reportes) aparecía como "0 reportes" en la herramienta.
    """
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True, "message": "OK",
        "data": {
            "encontrado": True,
            "numero": {
                "id": 365522, "telefono": "+34600123456", "total_reportes": 81, "total_consultas": 10,
                "nivel_peligro": "alto", "bloqueado": 0, "verificado": 0, "provincia": None,
                "operadora": "Vodafone", "notas": None,
                "primera_deteccion": "2026-04-11 09:08:21", "ultima_actualizacion": "2026-07-02 05:20:26",
                "tipo_spam": "spam", "tipo_descripcion": "Llamada publicitaria no solicitada",
                "tipo_color": "#FFA500", "tipo_spam_amigable": "Spam",
                "peligro_score": 70, "peligro_porcentaje": "70%", "peligro_nivel": "alto",
                "peligro_descripcion": "Riesgo alto. Bloquear o ignorar esta llamada.",
                "detalles": {"reportes_score": 100, "consultas_score": 30, "tipo_score": 20, "total_reportes": 81, "total_consultas": 10, "tipo_spam": "spam"},
            },
            "reportes_recientes": [],
            "recomendacion": "ADVERTENCIA: Número reportado múltiples veces. Bloquear recomendado. Además, se ha consultado 10 veces.",
            "_cache_hint": "Usa caché local (1-6 horas) para evitar límite de peticiones y mejorar rendimiento.",
        },
        "timestamp": "2026-07-24T08:36:19+02:00",
    }
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})

    data = response.json()
    assert data["community_reports"]["reports_count"] == 81
    assert data["community_reports"]["category"] == "spam"
    assert data["community_reports"]["danger_level"] == "alto"
    assert data["risk_score"] == 45
    assert "PHONE_COMMUNITY_REPORTED_HIGH" in [f["code"] for f in data["risk_flags"]]


def test_sin_ipqualityscore_key_degrada_con_gracia(client):
    response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})
    data = response.json()
    assert response.status_code == 200
    assert data["fraud_score"] is None
    assert any("IPQualityScore" in e for e in data["errors"])


def test_sin_credenciales_twilio_degrada_con_gracia(client):
    response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})
    data = response.json()
    assert response.status_code == 200
    assert data["carrier_intelligence"] is None
    assert any("Twilio" in e for e in data["errors"])


def test_ipqualityscore_fraud_score_alto_dispara_senal(client):
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True, "fraud_score": 95, "VOIP": True, "name": "No debería usarse"}
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.ipqualityscore_api_key", "fake-key"), \
         patch("app.services.ipqualityscore_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})

    data = response.json()
    assert data["fraud_score"]["fraud_score"] == 95
    assert "PHONE_HIGH_FRAUD_SCORE" in [f["code"] for f in data["risk_flags"]]
    assert "name" not in data["fraud_score"]


def test_twilio_lookup_detecta_voip_en_tiempo_real(client):
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"line_type_intelligence": {"carrier_name": "Carrier X", "type": "voip"}}
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.twilio_account_sid", "AC123"), \
         patch("app.core.config.settings.twilio_auth_token", "secret"), \
         patch("app.services.twilio_lookup_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34600123456", "default_region": "ES"})

    data = response.json()
    assert data["carrier_intelligence"]["line_type"] == "voip"
    assert "PHONE_VOIP_LIVE_MISMATCH" in [f["code"] for f in data["risk_flags"]]


def test_encontrado_false_da_cero_reportes(client):
    """La forma real de decir 'no encontrado' es data.encontrado=false, no solo un 404."""
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {"encontrado": False, "numero": None},
    }
    mock_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.openspam_api_key", "fake-key"), \
         patch("app.services.openspam_service.requests.get", return_value=mock_resp):
        response = client.post("/analysis/phone", json={"phone": "+34699999999", "default_region": "ES"})

    data = response.json()
    assert data["community_reports"]["reports_count"] == 0
    assert data["risk_flags"] == []
