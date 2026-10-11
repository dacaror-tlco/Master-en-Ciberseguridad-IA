"""
Fixtures compartidas. Igual que en scam-shield: un TestClient con la base
de datos sustituida por una SQLite en memoria, exclusiva de cada test, y
la ANTHROPIC_API_KEY forzada a vacío por defecto para que ningún test
haga una llamada real a la IA sin mockearla explícitamente.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.modules.reports import document, repository
from app.modules.reports.ai_narrative import Narrativa
from app.modules.shared.models import (
    Case,
    EstadoCaso,
    Evidence,
    OsintResult,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)

# Fase final (hardening): evita InsecureKeyLengthWarning de pyjwt (el
# jwt_secret por defecto, "change_me", tiene 9 bytes) sin tocar el .env
# real ni usar un secreto real — se sobreescribe en memoria el único
# Settings singleton del proceso de test.
settings.jwt_secret = "solo-para-tests-nunca-un-secreto-real-0123456789abcdef"
# La suite prueba el asistente contra su base SQLite de tests: leer el
# expediente por MCP lanzaría un proceso contra backends que aquí no existen.
# La vía MCP tiene sus propios tests (test_chat_fuente_mcp.py).
settings.chat_contexto = "sql"

NARRATIVA_FALSA = Narrativa(
    hallazgos="Se observa el evento inicial [E1] y su continuación [E2].",
    conclusiones="El incidente se considera acreditado en su alcance descrito.",
)

EMISION_FALSA = datetime(2026, 8, 15, 10, 30, tzinfo=timezone.utc)


def documento_de_prueba(db_session, caso, eventos=None, **extra):
    """El documento que reciben los renderizadores, montado desde la BD de test."""
    registro_osint = repository.get_registro_osint(db_session, caso.id)
    return document.construir_documento(
        case=caso,
        timeline_events=eventos
        if eventos is not None
        else repository.get_timeline_events(db_session, caso.id),
        narrativa=extra.pop("narrativa", NARRATIVA_FALSA),
        generado_por=extra.pop("generado_por", "Ana Pérez"),
        version=extra.pop("version", 1),
        generado_el=extra.pop("generado_el", EMISION_FALSA),
        evidences=repository.get_evidences(db_session, caso.id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(db_session, caso.id),
        **extra,
    )

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _configuracion_de_ia_fija():
    """
    Fija la configuración de IA para toda la suite, sin leer el `.env` local.

    Antes solo se anulaba la API key. En cuanto la narrativa del informe pudo
    venir de un modelo local, eso dejó de bastar: un `.env` de desarrollo con
    `NARRATIVA_PROVIDER=ollama` desviaba a la ruta local tests que mockean el
    cliente de Anthropic, y **la suite pasaba a llamar de verdad al modelo** —
    8 fallos y 20 minutos de ejecución en vez de 50 segundos.

    Los tests no pueden depender de cómo tenga cada uno configurada su máquina:
    quien quiera probar la ruta local la pide explícitamente parcheando
    `narrativa_provider` (ver `test_narrativa_local.py`).
    """
    with patch("app.core.config.settings.anthropic_api_key", ""), \
         patch("app.core.config.settings.narrativa_provider", "anthropic"), \
         patch("app.core.config.settings.chat_provider", "anthropic"):
        yield


@pytest.fixture(autouse=True)
def _base_datos_limpia():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def storage_dir(tmp_path):
    """
    Almacén de informes temporal, activo durante **todo** el test.

    `reports.archivo_pdf` guarda la ruta relativa al almacén, así que la
    configuración tiene que seguir en pie cuando se descarga, no solo cuando
    se genera. Parcheándolo solo alrededor de la generación, la descarga
    buscaría los ficheros en el almacén por defecto y respondería 410.
    """
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)):
        yield tmp_path


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _bearer_token(*, role: str = "analyst") -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + timedelta(hours=1)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@pytest.fixture
def client(db_session):
    """
    Fase 4: los 5 endpoints de este backend exigen autenticación, sin
    excepciones. Llega ya con un JWT de analyst válido por defecto — el
    resto de la suite prueba lógica de negocio, no auth en sí (eso vive
    en test_auth_reports.py, con un cliente sin esta cabecera).
    """
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {_bearer_token()}"
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def case_con_timeline(db_session):
    caso = Case(
        nombre="Caso de prueba",
        estado=EstadoCaso.EN_PROGRESO,
        fecha_creacion=datetime.now(timezone.utc) - timedelta(days=1),
        descripcion="Caso usado en tests",
        responsable="Tester",
    )
    db_session.add(caso)
    db_session.flush()

    base_time = datetime.now(timezone.utc)
    for i in range(3):
        db_session.add(
            TimelineEvent(
                id=f"tl-{i}",
                case_id=caso.id,
                fecha_hora=base_time + timedelta(hours=i),
                descripcion=f"Evento {i}",
                origen_modulo="tracking",
                origen_id=i,
                orden=i,
            )
        )
    db_session.commit()
    db_session.refresh(caso)
    return caso


@pytest.fixture
def case_con_anexos(db_session, case_con_timeline):
    """Caso con timeline más los registros de Módulos 1/2/3 que van a los anexos."""
    db_session.add(
        Evidence(
            case_id=case_con_timeline.id,
            tipo="imagen_disco",
            valor="EV-001 imagen forense del servidor web",
            fecha_subida=datetime.now(timezone.utc),
            observaciones="Adquirida en caliente",
        )
    )
    db_session.add(
        OsintResult(
            case_id=case_con_timeline.id,
            tipo_indicador="ip",
            valor="203.0.113.10",
            reputacion="maliciosa",
            pais="Países Bajos",
            detecciones=12,
            fuente="VirusTotal",
            fecha_consulta=datetime.now(timezone.utc),
            raw_response={"malicious": 12},
        )
    )
    db_session.add(
        TrackingEvent(
            id="evt-0001",
            case_id=case_con_timeline.id,
            hora=datetime.now(timezone.utc),
            evento="Ejecución de comandos de reconocimiento",
            severidad=Severidad.ALTA,
            fuente_log="auth.log",
            usuario_detectado="www-data",
        )
    )
    db_session.commit()
    return case_con_timeline
