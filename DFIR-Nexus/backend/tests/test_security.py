"""
Sección 16 de la tarea: comprobaciones específicas de seguridad sobre
Cases/Evidence. El proyecto no tiene autenticación (fuera de alcance,
CLAUDE.md), así que "autorización" aquí se limita a lo que sí es
comprobable sin usuarios: que un recurso no se pueda acceder/modificar a
través de un case_id que no es el suyo (IDOR de recurso hijo) y que los
campos de sistema (eliminado, hash_valor, fecha_actualizacion, etc.) no se
puedan fijar directamente desde el cliente (mass assignment).

Fase 3: estos endpoints ya exigen autenticación. Este fichero sigue
probando IDOR/mass-assignment, no auth — mismo patrón/justificación que
test_cases.py: `client` llega ya autenticado como admin.
"""
import pytest

from tests.conftest import PASSWORD_PRUEBA


@pytest.fixture
def client(client, admin):
    login = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


def crear_caso(client, **overrides):
    payload = {"nombre": "Caso A", "responsable": "Ana Pérez"}
    payload.update(overrides)
    return client.post("/cases", json=payload).json()


def crear_evidencia(client, case_id, **overrides):
    payload = {"tipo": "ip", "valor": "203.0.113.10"}
    payload.update(overrides)
    return client.post(f"/cases/{case_id}/evidences", json=payload).json()


# --- IDOR sobre el recurso hijo (Evidence a través de otro Case) -----------


def test_no_se_puede_modificar_evidencia_de_otro_caso(client):
    caso_a = crear_caso(client, nombre="Caso A")
    caso_b = crear_caso(client, nombre="Caso B")
    evidencia = crear_evidencia(client, caso_a["id"])

    r = client.put(
        f"/cases/{caso_b['id']}/evidences/{evidencia['id']}", json={"observaciones": "colada"}
    )
    assert r.status_code == 404


def test_no_se_puede_eliminar_evidencia_de_otro_caso(client):
    caso_a = crear_caso(client, nombre="Caso A")
    caso_b = crear_caso(client, nombre="Caso B")
    evidencia = crear_evidencia(client, caso_a["id"])

    r = client.delete(f"/cases/{caso_b['id']}/evidences/{evidencia['id']}")
    assert r.status_code == 404

    # La evidencia real, en su caso real, sigue intacta.
    r = client.get(f"/cases/{caso_a['id']}/evidences/{evidencia['id']}")
    assert r.status_code == 200
    assert r.json()["eliminado"] is False


# --- Mass assignment: campos de sistema no fijables por el cliente ---------


def test_no_se_puede_marcar_un_caso_eliminado_via_create_o_update(client):
    r = client.post(
        "/cases",
        json={"nombre": "Caso", "responsable": "Ana", "eliminado": True, "fecha_eliminacion": "2020-01-01"},
    )
    assert r.status_code == 201
    assert r.json()["eliminado"] is False

    caso = crear_caso(client)
    r = client.put(f"/cases/{caso['id']}", json={"eliminado": True})
    assert r.status_code == 200
    assert r.json()["eliminado"] is False  # el campo desconocido se ignora, no se aplica


def test_no_se_puede_fijar_hash_valor_ni_fecha_actualizacion_via_create_o_update(client):
    caso = crear_caso(client)
    r = client.post(
        f"/cases/{caso['id']}/evidences",
        json={
            "tipo": "ip",
            "valor": "203.0.113.10",
            "hash_valor": "0" * 64,
            "fecha_actualizacion": "2020-01-01T00:00:00",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["hash_valor"] != "0" * 64  # se recalcula server-side, el enviado se ignora

    r = client.put(
        f"/cases/{caso['id']}/evidences/{body['id']}", json={"hash_valor": "1" * 64}
    )
    assert r.status_code == 200
    assert r.json()["hash_valor"] == body["hash_valor"]  # inalterado


def test_no_se_puede_manipular_id_ajeno_via_body(client):
    """El id de la URL manda; un id distinto en el body no tiene efecto
    (EvidenceUpdate/CaseUpdate no declaran un campo `id`)."""
    caso = crear_caso(client)
    evidencia = crear_evidencia(client, caso["id"])

    r = client.put(
        f"/cases/{caso['id']}/evidences/{evidencia['id']}",
        json={"id": 999999, "observaciones": "x"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == evidencia["id"]
