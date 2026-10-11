"""
Fase 4: mecanismo OSINT -> Cases para POST /cases/{id}/auditoria/osint —
X-Service-Token (obligatorio) + JWT de usuario reenviado (opcional, solo
para resolver `actor`). Ver propuesta de identidad y acceso, secciones
11-12, y auth/dependencies.py::resolve_osint_actor.

No repite lo que ya prueba test_osint_audit.py (payload/escenarios de
vinculación en sí): esto prueba únicamente la capa de autenticación de
servicio añadida encima.
"""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from tests.conftest import auth_headers


def crear_caso(client, admin, **overrides):
    payload = {"nombre": "Caso A", "responsable": "Ana Pérez"}
    payload.update(overrides)
    headers = auth_headers(client, admin.email)
    return client.post("/cases", json=payload, headers=headers).json()


def _payload(case_id, **overrides):
    body = {"case_type": "ip", "source_id": 1, "case_anterior": None, "case_nuevo": case_id}
    body.update(overrides)
    return body


# --- rechazo sin X-Service-Token válido, con o sin JWT ----------------------


def test_sin_ninguna_cabecera_es_401(client, admin):
    caso = crear_caso(client, admin)
    r = client.post(f"/cases/{caso['id']}/auditoria/osint", json=_payload(caso["id"]))
    assert r.status_code == 401


def test_service_token_incorrecto_es_401(client, admin):
    caso = crear_caso(client, admin)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json=_payload(caso["id"]),
        headers={"X-Service-Token": "incorrecto"},
    )
    assert r.status_code == 401


def test_jwt_de_usuario_valido_sin_service_token_es_401(client, admin):
    """Un JWT de analyst/admin válido, por sí solo, NUNCA basta aquí — es
    justo lo que este mecanismo existe para impedir."""
    caso = crear_caso(client, admin)
    headers = auth_headers(client, admin.email)
    r = client.post(f"/cases/{caso['id']}/auditoria/osint", json=_payload(caso["id"]), headers=headers)
    assert r.status_code == 401


# --- aceptación con X-Service-Token válido, JWT opcional --------------------


def test_service_token_valido_sin_jwt_acepta_con_actor_osint(client, admin):
    caso = crear_caso(client, admin)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json=_payload(caso["id"]),
        headers={"X-Service-Token": settings.OSINT_AUDIT_SERVICE_TOKEN},
    )
    assert r.status_code == 201, r.text
    assert r.json()["actor"] == "osint"


def test_service_token_y_jwt_validos_resuelve_actor_real(client, admin):
    caso = crear_caso(client, admin)
    user_headers = auth_headers(client, admin.email)
    headers = {"X-Service-Token": settings.OSINT_AUDIT_SERVICE_TOKEN, **user_headers}
    r = client.post(f"/cases/{caso['id']}/auditoria/osint", json=_payload(caso["id"]), headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["actor"] == admin.nombre


def test_service_token_valido_con_jwt_caducado_degrada_a_actor_osint(client, admin):
    caso = crear_caso(client, admin)
    ahora = datetime.now(timezone.utc)
    token_caducado = jwt.encode(
        {
            "sub": str(admin.id),
            "role": "admin",
            "iat": ahora - timedelta(hours=3),
            "exp": ahora - timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    headers = {
        "X-Service-Token": settings.OSINT_AUDIT_SERVICE_TOKEN,
        "Authorization": f"Bearer {token_caducado}",
    }
    r = client.post(f"/cases/{caso['id']}/auditoria/osint", json=_payload(caso["id"]), headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["actor"] == "osint"


def test_service_token_valido_con_jwt_invalido_degrada_a_actor_osint(client, admin):
    caso = crear_caso(client, admin)
    headers = {
        "X-Service-Token": settings.OSINT_AUDIT_SERVICE_TOKEN,
        "Authorization": "Bearer no-es-un-jwt",
    }
    r = client.post(f"/cases/{caso['id']}/auditoria/osint", json=_payload(caso["id"]), headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["actor"] == "osint"
