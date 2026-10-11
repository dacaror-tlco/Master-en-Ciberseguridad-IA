"""
POST /cases/{case_id}/auditoria/osint — endpoint estrecho que usa OSINT
(scam-shield) por HTTP para dejar constancia en case_audit_log de un
cambio de vinculación de una investigación OSINT con un caso. Este
backend nunca toca las tablas de OSINT: solo registra la entrada de
auditoría que scam-shield le pide, ya con el cambio real persistido en su
lado.

Fase 4: el endpoint exige `X-Service-Token` (ver
test_osint_service_auth.py para la matriz completa de esa capa). Este
fichero sigue probando el payload/los escenarios de vinculación en sí,
así que cada llamada a `/auditoria/osint` adjunta el service token pero
deliberadamente NINGÚN JWT de usuario (`_sin_jwt_con_service_token`,
abajo) — así `actor` sigue resolviendo a "osint" como antes, sin mezclar
aquí la resolución del actor real (esa vive en test_osint_service_auth.py).
`POST /cases` (para crear los casos de prueba) sí exige autenticación
normal: usa el mismo `client` autenticado que test_cases.py.
"""
import pytest

from app.core.config import settings
from tests.conftest import PASSWORD_PRUEBA


@pytest.fixture
def client(client, admin):
    """Ver mismo patrón/justificación en test_cases.py."""
    login = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


def crear_caso(client, **overrides):
    payload = {"nombre": "Caso A", "responsable": "Ana Pérez"}
    payload.update(overrides)
    return client.post("/cases", json=payload).json()


def _sin_jwt_con_service_token(client) -> dict:
    """Quita el JWT de usuario que el fixture `client` lleva por defecto
    (necesario para crear_caso) y devuelve las cabeceras a usar en la
    llamada a /auditoria/osint: solo X-Service-Token, igual que haría
    OSINT cuando no puede resolver un usuario concreto."""
    client.headers.pop("Authorization", None)
    return {"X-Service-Token": settings.OSINT_AUDIT_SERVICE_TOKEN}


def test_vinculacion_null_a_caso(client):
    caso = crear_caso(client)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json={
            "case_type": "domain",
            "source_id": 7,
            "subject_value": "ejemplo-sospechoso.com",
            "case_anterior": None,
            "case_nuevo": caso["id"],
        },
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["case_id"] == caso["id"]
    assert body["evidence_id"] is None
    assert body["accion"] == "osint_vinculacion_cambiada"
    assert body["actor"] == "osint"
    assert body["detalle"] == {
        "case_type": "domain",
        "source_id": 7,
        "subject_value": "ejemplo-sospechoso.com",
        "de": None,
        "a": caso["id"],
    }


def test_vinculacion_caso_a_otro_caso_se_registra_en_el_caso_nuevo(client):
    caso_a = crear_caso(client, nombre="Caso A")
    caso_b = crear_caso(client, nombre="Caso B")
    r = client.post(
        f"/cases/{caso_b['id']}/auditoria/osint",
        json={
            "case_type": "ip",
            "source_id": 3,
            "case_anterior": caso_a["id"],
            "case_nuevo": caso_b["id"],
        },
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 201, r.text
    assert r.json()["case_id"] == caso_b["id"]
    assert r.json()["detalle"]["de"] == caso_a["id"]
    assert r.json()["detalle"]["a"] == caso_b["id"]


def test_vinculacion_caso_a_null_se_registra_en_el_caso_anterior(client):
    caso = crear_caso(client)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json={
            "case_type": "wallet",
            "source_id": 9,
            "case_anterior": caso["id"],
            "case_nuevo": None,
        },
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 201, r.text
    assert r.json()["case_id"] == caso["id"]
    assert r.json()["detalle"]["de"] == caso["id"]
    assert r.json()["detalle"]["a"] is None


def test_entrada_aparece_en_get_auditoria_del_caso(client, admin):
    caso = crear_caso(client)
    headers = _sin_jwt_con_service_token(client)
    client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json={"case_type": "email", "source_id": 1, "case_anterior": None, "case_nuevo": caso["id"]},
        headers=headers,
    )
    # GET /cases/{id}/auditoria sí exige un usuario autenticado (Fase 3):
    # se vuelve a autenticar tras haber quitado el JWT arriba.
    login = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    r = client.get(f"/cases/{caso['id']}/auditoria")
    acciones = [e["accion"] for e in r.json()]
    assert "osint_vinculacion_cambiada" in acciones


def test_caso_inexistente_devuelve_404(client):
    r = client.post(
        "/cases/999999/auditoria/osint",
        json={"case_type": "domain", "source_id": 1, "case_anterior": None, "case_nuevo": 999999},
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 404


def test_case_anterior_y_case_nuevo_ambos_nulos_es_invalido(client):
    caso = crear_caso(client)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json={"case_type": "domain", "source_id": 1, "case_anterior": None, "case_nuevo": None},
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 422


def test_case_id_de_la_url_debe_coincidir_con_anterior_o_nuevo(client):
    caso_a = crear_caso(client, nombre="Caso A")
    caso_b = crear_caso(client, nombre="Caso B")
    otro = crear_caso(client, nombre="Otro")
    r = client.post(
        f"/cases/{otro['id']}/auditoria/osint",
        json={
            "case_type": "domain",
            "source_id": 1,
            "case_anterior": caso_a["id"],
            "case_nuevo": caso_b["id"],
        },
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 422


# --- Fase 4: NO debe quedar protegido como un endpoint normal de usuario ---


def test_endpoint_osint_funciona_sin_jwt_de_usuario_pero_exige_service_token(client):
    """A diferencia de cualquier otro endpoint de Cases (todos exigen un
    JWT de usuario desde la Fase 3), este acepta la llamada sin ninguna
    cabecera Authorization — pero, a partir de la Fase 4, SÍ exige
    X-Service-Token; sin él, 401 (ver test_osint_service_auth.py)."""
    caso = crear_caso(client)
    r = client.post(
        f"/cases/{caso['id']}/auditoria/osint",
        json={"case_type": "ip", "source_id": 1, "case_anterior": None, "case_nuevo": caso["id"]},
        headers=_sin_jwt_con_service_token(client),
    )
    assert r.status_code == 201, r.text
