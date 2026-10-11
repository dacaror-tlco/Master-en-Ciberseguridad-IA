"""
El asistente conversacional también exige JWT (a nivel de router, ver
app/main.py). Hermano de test_auth_reports.py, y aparte a propósito: el
chat es la ruta de este backend que más contexto expone de una sola vez
—el expediente completo de un caso viaja en el prompt— así que su capa de
autenticación se prueba explícitamente en vez de darse por cubierta
porque «está en el mismo router de siempre».

Dos comprobaciones que no son obvias y son el motivo de este fichero:

1. `POST /chat/stream` devuelve el 401 como código HTTP, no como evento
   `error` del flujo. La dependencia se evalúa antes de que empiece a
   emitirse nada, así que la cabecera todavía no ha salido — que es lo que
   permite al frontend tratarlo como sesión caducada (ver chatApi.ts).
2. Ninguno de los 401 llega a llamar al modelo. Con `chat_provider` fijado
   a "anthropic" y la API key vacía (ver conftest.py), una llamada real se
   vería como un 503, no como un 401.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app

PREGUNTA = {"mensaje": "¿Qué es una cadena de custodia?", "case_id": None, "historial": []}


def _token(*, role: str = "analyst", exp_delta: timedelta = timedelta(hours=1)) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + exp_delta}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@pytest.fixture
def anon_client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_chat_sin_token_es_401(anon_client):
    assert anon_client.post("/chat", json=PREGUNTA).status_code == 401


def test_stream_sin_token_es_401(anon_client):
    """Y como 401 HTTP, no como evento `error` dentro del flujo."""
    respuesta = anon_client.post("/chat/stream", json=PREGUNTA)
    assert respuesta.status_code == 401
    assert "text/event-stream" not in respuesta.headers.get("content-type", "")


def test_chat_con_token_invalido_es_401(anon_client):
    respuesta = anon_client.post(
        "/chat", json=PREGUNTA, headers={"Authorization": "Bearer no-es-un-jwt"}
    )
    assert respuesta.status_code == 401


def test_chat_con_token_caducado_es_401(anon_client):
    token = _token(exp_delta=timedelta(hours=-1))
    respuesta = anon_client.post(
        "/chat", json=PREGUNTA, headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 401


def test_sin_token_no_se_llama_al_modelo(anon_client):
    """
    El 401 se resuelve en la dependencia, antes del servicio. Si no fuese
    así, con la API key vacía de la suite esto sería un 503 de
    configuración — o, peor, una llamada real a la IA.
    """
    respuesta = anon_client.post("/chat", json={**PREGUNTA, "case_id": 999})
    assert respuesta.status_code == 401


def test_analyst_autenticado_pasa_la_autorizacion(anon_client):
    """
    404 y no 401: el caso 999 no existe, pero la petición ya había
    superado la autenticación. El aislamiento por caso (que es lo que
    protege de *leer otro* caso) se prueba en
    test_aislamiento_entre_casos.py.
    """
    respuesta = anon_client.post(
        "/chat",
        json={**PREGUNTA, "case_id": 999},
        headers={"Authorization": f"Bearer {_token()}"},
    )
    assert respuesta.status_code == 404


def test_admin_autenticado_tambien_pasa(anon_client):
    """Sin endpoints admin en este backend: el rol no restringe el chat."""
    respuesta = anon_client.post(
        "/chat",
        json={**PREGUNTA, "case_id": 999},
        headers={"Authorization": f"Bearer {_token(role='admin')}"},
    )
    assert respuesta.status_code == 404
