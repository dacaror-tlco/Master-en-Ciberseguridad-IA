"""
Fixtures compartidas por todos los tests.

La pieza clave es `client`: un TestClient de FastAPI con la base de datos
sustituida por una SQLite en memoria, exclusiva de cada test (se crea
vacía al principio y se destruye al final). Así los tests nunca tocan tu
scamshield.db real ni se contaminan entre sí.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import case, email_case, wallet_case  # noqa: F401 - registra los modelos en Base
from app.schemas.domain_analysis import SSLCertInfo, VirusTotalInfo, WhoisInfo


_EXTERNAL_API_SETTINGS = [
    "virustotal_api_key", "abuseipdb_api_key", "etherscan_api_key", "tron_api_key", "anthropic_api_key", "openspam_api_key",
    "serpapi_api_key", "pimeyes_api_key", "ipqualityscore_api_key",
    "twilio_account_sid", "twilio_auth_token", "public_base_url",
    "fca_api_email", "fca_api_key",
]


@pytest.fixture(autouse=True)
def _sin_api_keys_reales_por_defecto():
    """
    `Settings` lee `.env` de verdad al arrancar — si el desarrollador tiene
    alguna key real configurada ahí (para probar la app a mano), esa key
    "se cuela" en cualquier test que no la mockee explícitamente, haciendo
    una llamada de red real y con resultados no deterministas (justo lo
    que el resto de la suite evita a propósito, ver README). Este autouse
    fuerza todas las keys externas a vacío por defecto; los tests que sí
    quieran probar la integración configurada la sobreescriben con su
    propio `patch("app.core.config.settings.xxx_api_key", "fake-key")`.
    """
    patches = [patch(f"app.core.config.settings.{name}", "") for name in _EXTERNAL_API_SETTINGS]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()


@pytest.fixture(autouse=True)
def _no_real_dns_resolution():
    """
    El módulo de dominio resuelve todas las IPs del dominio (para
    DNS/AbuseIPDB) con `dns_service.get_dns_records`, que hace una
    resolución DNS real. Sin este autouse, cualquier test que analice un
    dominio (aunque no le interese la IP) haría una consulta DNS real de
    verdad — justo lo que el resto de la suite evita a propósito (ver
    README, "Por qué está diseñado así"). Por defecto simula "no se pudo
    resolver" (como un NXDOMAIN real); los tests que sí quieran probar la
    resolución la sobreescriben con su propio `patch`.
    """
    with patch("app.services.dns_service.get_dns_records", side_effect=Exception("DNS deshabilitado en tests (ver conftest)")):
        yield


@pytest.fixture(autouse=True)
def _no_real_crtsh_lookup():
    """
    `crtsh_service.get_crtsh_info` consulta crt.sh (Certificate
    Transparency) por HTTP de verdad — sin este autouse, cualquier test
    que analice un dominio haría esa petición real (lenta y, se ha
    comprobado a mano, con fallos intermitentes incluso para consultas
    válidas: no es algo con lo que la suite deba depender para pasar).
    """
    with patch("app.services.crtsh_service.get_crtsh_info", side_effect=Exception("crt.sh deshabilitado en tests (ver conftest)")):
        yield


@pytest.fixture(autouse=True)
def _no_real_wayback_lookup():
    """
    Igual que crt.sh: `wayback_service.get_wayback_info` consulta el CDX
    API de Internet Archive por HTTP de verdad.
    """
    with patch("app.services.wayback_service.get_wayback_info", side_effect=Exception("Wayback deshabilitado en tests (ver conftest)")):
        yield


@pytest.fixture(autouse=True)
def _no_real_cnmv_registry_lookup():
    """
    `cnmv_registry_service.search_registered_entities` hace un scraping
    real (GET+POST) contra la web de la CNMV — sin este autouse, cualquier
    test de verificación CNMV que no lo mockee explícitamente haría esa
    petición real. `return_value=None` reproduce "la comprobación no se
    llegó a hacer" (no dispara la señal de ausencia), el mismo estado que
    tendría un caso analizado antes de que existiera esta función.
    """
    with patch("app.services.cnmv_registry_service.search_registered_entities", return_value=None):
        yield


@pytest.fixture(autouse=True)
def _no_real_ofac_list_download():
    """
    `ofac_service.ensure_cache_fresh` descarga 3 ficheros reales de GitHub
    en cada análisis de wallet cuando la caché está vacía/caducada — sin
    este autouse, cualquier test de wallet haría esas peticiones reales.
    `return_value=[]` reproduce "no hacía falta refrescar" (mismo estado
    que una caché ya fresca); los tests que sí quieran probar el cruce
    OFAC mockean `ofac_service.is_sanctioned` directamente.
    """
    with patch("app.services.ofac_service.ensure_cache_fresh", return_value=[]):
        yield


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    test_client.test_engine = engine  # acceso directo para tests que necesiten simular manipulación de la BD (cadena de custodia)
    yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(client):
    """
    Sesión SQLAlchemy directa sobre la misma base en memoria que usa `client`.
    Útil para tests unitarios de servicios (p.ej. monitoring_service) que
    necesitan una Session real sin pasar por la API HTTP.
    """
    session = sessionmaker(bind=client.test_engine)()
    yield session
    session.close()


# ---------------------------------------------------------------------
# Datos simulados reutilizables (evitan repetir el mismo dict en cada test)
# ---------------------------------------------------------------------

@pytest.fixture()
def fresh_whois():
    """WHOIS de un dominio recién registrado (típico de phishing)."""
    return WhoisInfo(
        registrar=None,
        creation_date=datetime.now(timezone.utc) - timedelta(days=3),
        domain_age_days=3,
        country="XX",
        name_servers=[],
    )


@pytest.fixture()
def old_whois():
    """WHOIS de un dominio antiguo y legítimo."""
    return WhoisInfo(
        registrar="Registrar Legit Inc",
        creation_date=datetime.now(timezone.utc) - timedelta(days=3000),
        domain_age_days=3000,
        country="ES",
        name_servers=["ns1.example.com"],
    )


@pytest.fixture()
def fresh_ssl():
    return SSLCertInfo(has_valid_cert=True, issuer="FakeCA", days_since_issued=1, subject_alt_names=[])


@pytest.fixture()
def old_ssl():
    return SSLCertInfo(has_valid_cert=True, issuer="Let's Encrypt", days_since_issued=500, subject_alt_names=[])


@pytest.fixture()
def clean_vt():
    return VirusTotalInfo(malicious_count=0, suspicious_count=0, harmless_count=70, undetected_count=5)


@pytest.fixture()
def flagged_vt():
    return VirusTotalInfo(malicious_count=8, suspicious_count=2, harmless_count=60, undetected_count=10, categories=["phishing"])


PHISHING_EMAIL_RAW = """From: Banco Seguro <soporte@banco-seguro-verificacion.xyz>
Reply-To: recuperacion@otro-dominio-raro.com
Subject: Tu cuenta ha sido bloqueada
Date: Wed, 09 Jul 2026 10:00:00 +0000
Authentication-Results: mx.google.com; spf=fail; dkim=fail; dmarc=fail
Received: from mail.banco-seguro-verificacion.xyz (unknown [203.0.113.55]) by mx.google.com; Wed, 09 Jul 2026 10:00:01 +0000

Cuerpo del mensaje.
"""

LEGIT_EMAIL_RAW = """From: Notificaciones <no-reply@empresa-legitima.com>
Subject: Tu factura mensual
Date: Wed, 09 Jul 2026 10:00:00 +0000
Authentication-Results: mx.google.com; spf=pass; dkim=pass; dmarc=pass
Received: from mail.empresa-legitima.com (mail.empresa-legitima.com [198.51.100.10]) by mx.google.com; Wed, 09 Jul 2026 10:00:01 +0000

Aqui tienes tu factura.
"""
