"""
Autenticación (Fase 4 de `development`, traída a este módulo): los cinco
endpoints de este backend exigen un JWT emitido por el backend de Casos.

Aquí no se repite lógica de negocio —de eso se encarga el resto de la
suite, que entra con el cliente ya autenticado de conftest.py—: esto
prueba únicamente la capa que se añade por encima, incluido lo que debe
seguir siendo público y el modo "módulo suelto".

No hay escenarios 403: en este backend ningún endpoint pide rol admin
(ver matriz de permisos de la Fase 4).
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from .conftest import crear_caso, token_de_prueba

LOG = "2026-08-14 03:11:19  whoami\n"


@pytest.fixture
def anonimo():
    """Cliente SIN cabecera de autorización: el navegador de alguien que no
    ha iniciado sesión, o una sesión ya caducada."""
    with TestClient(app) as c:
        yield c


def _autorizacion(**kwargs) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de_prueba(**kwargs)}"}


# --------------------------------------------------------------- sin token

def test_cases_lookup_sin_token_es_401(anonimo):
    assert anonimo.get("/cases-lookup").status_code == 401


def test_listar_eventos_sin_token_es_401(anonimo):
    assert anonimo.get("/cases/1/tracking/events").status_code == 401


def test_verificar_integridad_sin_token_es_401(anonimo):
    assert anonimo.get("/cases/1/tracking/verify").status_code == 401


def test_analizar_sin_token_es_401(anonimo):
    r = anonimo.post("/cases/1/tracking/analyze", files={"file": ("x.log", LOG, "text/plain")})
    assert r.status_code == 401


def test_guardar_sin_token_es_401(anonimo):
    """El más importante de los cinco: sin esto, cualquiera que llegue al
    puerto del backend puede escribir en `tracking_events`."""
    cuerpo = {"case_id": 1, "fuente_log": "a.log",
              "eventos": [{"hora": "2026-08-14T03:11:19Z", "evento": "whoami", "severidad": "baja"}]}
    assert anonimo.post("/cases/1/tracking/events", json=cuerpo).status_code == 401


# ------------------------------------------------------------ token inválido

def test_token_que_no_es_un_jwt_es_401(anonimo):
    r = anonimo.get("/cases-lookup", headers={"Authorization": "Bearer esto-no-es-un-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token inválido"


def test_token_caducado_es_401(anonimo):
    r = anonimo.get("/cases-lookup", headers=_autorizacion(caduca_en=timedelta(hours=-1)))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expirado"


def test_token_firmado_con_otro_secreto_es_401(anonimo):
    """Un token bien formado pero de otra instalación no vale: es la firma,
    no el formato, lo que autoriza."""
    import jwt
    from datetime import datetime, timezone

    ahora = datetime.now(timezone.utc)
    ajeno = jwt.encode(
        {"sub": "1", "role": "admin", "iat": ahora, "exp": ahora + timedelta(hours=1)},
        "otro-secreto-distinto-del-de-casos",
        algorithm="HS256",
    )
    assert anonimo.get("/cases-lookup", headers={"Authorization": f"Bearer {ajeno}"}).status_code == 401


def test_cabecera_sin_bearer_es_401(anonimo):
    r = anonimo.get("/cases-lookup", headers={"Authorization": token_de_prueba()})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token no proporcionado"


# -------------------------------------------------------------- token válido

@pytest.mark.parametrize("role", ["analyst", "admin"])
def test_con_token_valido_se_entra(anonimo, role):
    assert anonimo.get("/cases-lookup", headers=_autorizacion(role=role)).status_code == 200


def test_el_flujo_completo_funciona_con_token(anonimo):
    """Analizar, guardar y verificar con el token puesto: la autenticación
    no cambia el comportamiento de los endpoints, solo el acceso."""
    case_id = crear_caso("Con token", "perito")
    cabeceras = _autorizacion()

    analisis = anonimo.post(
        f"/cases/{case_id}/tracking/analyze",
        files={"file": ("a.log", LOG, "text/plain")},
        headers=cabeceras,
    )
    assert analisis.status_code == 200

    guardado = anonimo.post(
        f"/cases/{case_id}/tracking/events",
        json={"case_id": case_id, "fuente_log": "a.log",
              "eventos": [{"hora": "2026-08-14T03:11:19Z", "evento": "whoami", "severidad": "baja"}]},
        headers=cabeceras,
    )
    assert guardado.status_code == 200 and guardado.json()["guardados"] == 1
    assert anonimo.get(f"/cases/{case_id}/tracking/verify", headers=cabeceras).json()["ok"] is True


# ------------------------------------------------------- lo que sigue público

def test_la_documentacion_y_el_frontend_no_piden_token(anonimo):
    """La autenticación va en los routers de la API, no en la aplicación:
    la documentación y la pantalla que se sirve al navegador siguen
    abiertas (el token lo pone el frontend DESPUÉS, en cada llamada)."""
    assert anonimo.get("/docs").status_code == 200
    assert anonimo.get("/").status_code == 200


def test_el_preflight_de_cors_no_pide_token(anonimo):
    """El navegador manda el OPTIONS previo SIN cabecera de autorización: si
    exigiera token, el frontend no podría ni empezar a hablar con la API."""
    r = anonimo.options(
        "/cases/1/tracking/events",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert r.status_code == 200
    assert "authorization" in r.headers.get("access-control-allow-headers", "").lower()


# --------------------------------------------------- modo "módulo suelto"

def test_con_la_autenticacion_desactivada_se_entra_sin_token(anonimo, monkeypatch):
    """Arrancando el módulo por su cuenta no hay backend de Casos que emita
    tokens ni pantalla de login: el interruptor existe para eso."""
    monkeypatch.setenv("TRACKING_AUTH_DESACTIVADA", "1")
    assert anonimo.get("/cases-lookup").status_code == 200


def test_el_interruptor_solo_vale_con_un_valor_afirmativo(anonimo, monkeypatch):
    """Que una variable a 0 o vacía no apague la autenticación por descuido."""
    for valor in ("0", "", "false", "no"):
        monkeypatch.setenv("TRACKING_AUTH_DESACTIVADA", valor)
        assert anonimo.get("/cases-lookup").status_code == 401, valor
