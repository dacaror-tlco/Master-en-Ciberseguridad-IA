"""
Ciclo de vida de Case: CRUD, borrado lógico (P0.1), máquina de estados (P1)
y auditoría (P1). Prueban comportamiento real observable vía API, no
alcance de líneas.
"""
import pytest

from tests.conftest import PASSWORD_PRUEBA


@pytest.fixture
def client(client, admin):
    """
    Sobrescribe, solo en este fichero, el `client` de conftest.py (patrón
    estándar de pytest para extender una fixture: una fixture puede
    depender de otra con su mismo nombre, que pytest resuelve a la del
    conftest padre). Este módulo prueba el CRUD de Case/Evidence — no
    autenticación/autorización, que vive en test_auth.py — así que aquí
    el cliente llega ya autenticado como admin (superset de analyst, ver
    dependencies.require_admin) para no repetir cabeceras en cada
    llamada. Los escenarios 401/403 de estos mismos endpoints se prueban
    aparte, en test_auth_cases.py, con el `client` sin autenticar.
    """
    login = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


def crear_caso(client, **overrides):
    payload = {"nombre": "Intrusión en servidor web", "responsable": "Ana Pérez"}
    payload.update(overrides)
    return client.post("/cases", json=payload)


# --- CRUD básico -------------------------------------------------------


def test_crear_caso(client):
    r = crear_caso(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["estado"] == "abierto"
    assert body["eliminado"] is False
    assert body["fecha_eliminacion"] is None
    assert "fecha_actualizacion" in body


def test_consultar_caso(client):
    creado = crear_caso(client).json()
    r = client.get(f"/cases/{creado['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == creado["id"]


def test_consultar_caso_inexistente(client):
    r = client.get("/cases/999999")
    assert r.status_code == 404


def test_listar_casos(client):
    crear_caso(client, nombre="Caso A")
    crear_caso(client, nombre="Caso B")
    r = client.get("/cases")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_actualizar_caso(client):
    creado = crear_caso(client).json()
    r = client.put(f"/cases/{creado['id']}", json={"descripcion": "Actualizado"})
    assert r.status_code == 200
    assert r.json()["descripcion"] == "Actualizado"


def test_actualizar_caso_inexistente(client):
    r = client.put("/cases/999999", json={"descripcion": "x"})
    assert r.status_code == 404


# --- P0.1: DELETE de Case ------------------------------------------------


def test_delete_caso_es_borrado_logico_no_500(client):
    """Bug original: DELETE devolvía 500 sin control. Ahora debe
    completarse con 204 y el caso debe seguir existiendo (eliminado=True),
    no haber desaparecido físicamente."""
    creado = crear_caso(client).json()

    r = client.delete(f"/cases/{creado['id']}")
    assert r.status_code == 204, r.text

    r = client.get(f"/cases/{creado['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["eliminado"] is True
    assert body["fecha_eliminacion"] is not None


def test_delete_caso_inexistente(client):
    r = client.delete("/cases/999999")
    assert r.status_code == 404


def test_delete_caso_ya_eliminado_devuelve_409(client):
    creado = crear_caso(client).json()
    client.delete(f"/cases/{creado['id']}")
    r = client.delete(f"/cases/{creado['id']}")
    assert r.status_code == 409


def test_caso_eliminado_desaparece_del_listado_por_defecto(client):
    creado = crear_caso(client).json()
    client.delete(f"/cases/{creado['id']}")

    r = client.get("/cases")
    assert creado["id"] not in [c["id"] for c in r.json()]

    r = client.get("/cases?incluir_eliminados=true")
    assert creado["id"] in [c["id"] for c in r.json()]


def test_delete_caso_con_evidencia_no_da_500_y_marca_la_evidencia_eliminada(client):
    """Caso concreto que producía el 500 original cuando el caso tenía
    dependientes (aquí, su propia evidencia)."""
    creado = crear_caso(client).json()
    ev = client.post(
        f"/cases/{creado['id']}/evidences", json={"tipo": "ip", "valor": "203.0.113.10"}
    ).json()

    r = client.delete(f"/cases/{creado['id']}")
    assert r.status_code == 204, r.text

    r = client.get(f"/cases/{creado['id']}/evidences/{ev['id']}")
    assert r.status_code == 200
    assert r.json()["eliminado"] is True


def test_no_se_puede_modificar_un_caso_eliminado(client):
    creado = crear_caso(client).json()
    client.delete(f"/cases/{creado['id']}")

    r = client.put(f"/cases/{creado['id']}", json={"descripcion": "no debería aplicarse"})
    assert r.status_code == 409


def test_no_se_puede_anadir_evidencia_a_un_caso_eliminado(client):
    creado = crear_caso(client).json()
    client.delete(f"/cases/{creado['id']}")

    r = client.post(f"/cases/{creado['id']}/evidences", json={"tipo": "ip", "valor": "1.2.3.4"})
    assert r.status_code == 409


# --- P1: máquina de estados ----------------------------------------------


def test_transicion_de_estado_valida(client):
    creado = crear_caso(client).json()
    r = client.put(f"/cases/{creado['id']}", json={"estado": "en_progreso"})
    assert r.status_code == 200
    assert r.json()["estado"] == "en_progreso"


def test_transicion_de_estado_invalida_devuelve_409(client):
    """abierto -> archivado es válida, pero archivado -> abierto NO: un
    caso archivado es terminal."""
    creado = crear_caso(client).json()
    client.put(f"/cases/{creado['id']}", json={"estado": "archivado"})

    r = client.put(f"/cases/{creado['id']}", json={"estado": "abierto"})
    assert r.status_code == 409


def test_caso_archivado_es_inmutable(client):
    creado = crear_caso(client).json()
    client.put(f"/cases/{creado['id']}", json={"estado": "archivado"})

    r = client.put(f"/cases/{creado['id']}", json={"descripcion": "no debería aplicarse"})
    assert r.status_code == 409


def test_transicion_al_mismo_estado_es_idempotente(client):
    creado = crear_caso(client).json()
    r = client.put(f"/cases/{creado['id']}", json={"estado": "abierto"})
    assert r.status_code == 200


# --- P1: auditoría ---------------------------------------------------------


def test_auditoria_registra_creacion_actualizacion_cambio_estado_y_borrado(client):
    creado = crear_caso(client).json()
    client.put(f"/cases/{creado['id']}", json={"descripcion": "actualizado"})
    client.put(f"/cases/{creado['id']}", json={"estado": "en_progreso"})
    client.delete(f"/cases/{creado['id']}")

    r = client.get(f"/cases/{creado['id']}/auditoria")
    assert r.status_code == 200
    acciones = [entrada["accion"] for entrada in r.json()]

    assert "case_creado" in acciones
    assert "case_actualizado" in acciones
    assert "case_estado_cambiado" in acciones
    assert "case_eliminado" in acciones

    cambio_estado = next(e for e in r.json() if e["accion"] == "case_estado_cambiado")
    assert cambio_estado["detalle"] == {"de": "abierto", "a": "en_progreso"}
    assert all(e["case_id"] == creado["id"] for e in r.json())


def test_auditoria_de_caso_inexistente_devuelve_404(client):
    r = client.get("/cases/999999/auditoria")
    assert r.status_code == 404
