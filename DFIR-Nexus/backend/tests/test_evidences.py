"""
Ciclo de vida de Evidence: CRUD, integridad (hash), inmutabilidad de
tipo/valor, borrado lógico y relación con Case.
"""
import pytest

from tests.conftest import PASSWORD_PRUEBA


@pytest.fixture
def client(client, admin):
    """Ver mismo patrón/justificación en test_cases.py."""
    login = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


def crear_caso(client, **overrides):
    payload = {"nombre": "Intrusión en servidor web", "responsable": "Ana Pérez"}
    payload.update(overrides)
    return client.post("/cases", json=payload).json()


def crear_evidencia(client, case_id, **overrides):
    payload = {"tipo": "ip", "valor": "203.0.113.10"}
    payload.update(overrides)
    return client.post(f"/cases/{case_id}/evidences", json=payload)


# --- CRUD básico -----------------------------------------------------------


def test_crear_evidencia(client):
    caso = crear_caso(client)
    r = crear_evidencia(client, caso["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["case_id"] == caso["id"]
    assert len(body["hash_valor"]) == 64
    assert body["eliminado"] is False


def test_crear_evidencia_bajo_caso_inexistente(client):
    r = crear_evidencia(client, 999999)
    assert r.status_code == 404


def test_consultar_evidencia(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()
    r = client.get(f"/cases/{caso['id']}/evidences/{creada['id']}")
    assert r.status_code == 200


def test_consultar_evidencia_inexistente(client):
    caso = crear_caso(client)
    r = client.get(f"/cases/{caso['id']}/evidences/999999")
    assert r.status_code == 404


def test_consultar_evidencia_de_otro_caso_da_404(client):
    """Una evidencia no debe poder consultarse a través de un case_id que
    no es el suyo, aunque el id de evidencia exista."""
    caso_a = crear_caso(client, nombre="Caso A")
    caso_b = crear_caso(client, nombre="Caso B")
    evidencia = crear_evidencia(client, caso_a["id"]).json()

    r = client.get(f"/cases/{caso_b['id']}/evidences/{evidencia['id']}")
    assert r.status_code == 404


def test_listar_evidencias_de_un_caso(client):
    caso = crear_caso(client)
    crear_evidencia(client, caso["id"], tipo="ip", valor="1.1.1.1")
    crear_evidencia(client, caso["id"], tipo="dominio", valor="example.com")
    r = client.get(f"/cases/{caso['id']}/evidences")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_actualizar_observaciones_de_evidencia(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()
    r = client.put(
        f"/cases/{caso['id']}/evidences/{creada['id']}", json={"observaciones": "verificado"}
    )
    assert r.status_code == 200
    assert r.json()["observaciones"] == "verificado"


def test_actualizar_evidencia_inexistente(client):
    caso = crear_caso(client)
    r = client.put(f"/cases/{caso['id']}/evidences/999999", json={"observaciones": "x"})
    assert r.status_code == 404


# --- P1: integridad (hash) --------------------------------------------------


def test_update_no_admite_cambiar_tipo_ni_valor(client):
    """tipo/valor son el contenido probatorio: inmutable tras crear la
    evidencia. Un intento de "colarlos" en el PUT se ignora silenciosamente
    (Pydantic los descarta por no estar en EvidenceUpdate), no rompe nada,
    pero el valor original debe conservarse intacto."""
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"], valor="203.0.113.10").json()

    r = client.put(
        f"/cases/{caso['id']}/evidences/{creada['id']}",
        json={"valor": "manipulado", "tipo": "otro", "observaciones": "nota"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valor"] == "203.0.113.10"
    assert body["tipo"] == "ip"
    assert body["observaciones"] == "nota"


def test_verificar_integridad_de_evidencia_no_manipulada(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"], valor="203.0.113.10").json()

    r = client.get(f"/cases/{caso['id']}/evidences/{creada['id']}/integridad")
    assert r.status_code == 200
    body = r.json()
    assert body["integro"] is True
    assert body["hash_registrado"] == body["hash_actual"]
    assert body["algoritmo"] == "sha256"


def test_hash_es_estable_entre_dos_evidencias_con_el_mismo_valor(client):
    caso = crear_caso(client)
    a = crear_evidencia(client, caso["id"], valor="mismo-valor").json()
    b = crear_evidencia(client, caso["id"], valor="mismo-valor").json()
    assert a["hash_valor"] == b["hash_valor"]


def test_hash_distingue_valores_distintos(client):
    caso = crear_caso(client)
    a = crear_evidencia(client, caso["id"], valor="valor-a").json()
    b = crear_evidencia(client, caso["id"], valor="valor-b").json()
    assert a["hash_valor"] != b["hash_valor"]


# --- P0/P1: borrado lógico y relación con Case ------------------------------


def test_delete_evidencia_es_borrado_logico(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()

    r = client.delete(f"/cases/{caso['id']}/evidences/{creada['id']}")
    assert r.status_code == 204

    r = client.get(f"/cases/{caso['id']}/evidences/{creada['id']}")
    assert r.status_code == 200
    assert r.json()["eliminado"] is True


def test_delete_evidencia_ya_eliminada_devuelve_409(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()
    client.delete(f"/cases/{caso['id']}/evidences/{creada['id']}")

    r = client.delete(f"/cases/{caso['id']}/evidences/{creada['id']}")
    assert r.status_code == 409


def test_evidencia_eliminada_desaparece_del_listado_por_defecto(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()
    client.delete(f"/cases/{caso['id']}/evidences/{creada['id']}")

    r = client.get(f"/cases/{caso['id']}/evidences")
    assert creada["id"] not in [e["id"] for e in r.json()]

    r = client.get(f"/cases/{caso['id']}/evidences?incluir_eliminados=true")
    assert creada["id"] in [e["id"] for e in r.json()]


def test_no_puede_quedar_evidencia_huerfana_de_un_caso_inexistente(client):
    """No existe endpoint para crear evidencia sin pasar por un case_id
    válido: se comprueba explícitamente en cada operación."""
    r = crear_evidencia(client, 999999)
    assert r.status_code == 404
    r = client.get("/cases/999999/evidences")
    assert r.status_code == 404


def test_auditoria_registra_operaciones_sobre_evidencia(client):
    caso = crear_caso(client)
    creada = crear_evidencia(client, caso["id"]).json()
    client.put(f"/cases/{caso['id']}/evidences/{creada['id']}", json={"observaciones": "x"})
    client.delete(f"/cases/{caso['id']}/evidences/{creada['id']}")

    r = client.get(f"/cases/{caso['id']}/auditoria")
    entradas = [e for e in r.json() if e["evidence_id"] == creada["id"]]
    acciones = [e["accion"] for e in entradas]
    assert "evidence_creada" in acciones
    assert "evidence_actualizada" in acciones
    assert "evidence_eliminada" in acciones
