"""
Fase 3: autorización real aplicada a los endpoints de Cases/Evidences —
sin JWT -> 401, JWT inválido/caducado -> 401, rol insuficiente -> 403,
analyst en operación normal -> éxito, admin en operación administrativa ->
éxito. No repite lo que ya prueba test_cases.py/test_evidences.py (esos
ficheros ya cubren la lógica de negocio en sí, con un cliente admin por
defecto): este fichero prueba únicamente la capa de autenticación/
autorización añadida encima, con el `client` SIN autenticar de
conftest.py.
"""
from tests.conftest import PASSWORD_PRUEBA, auth_headers


def crear_caso_como_admin(client, admin, **overrides):
    payload = {"nombre": "Intrusión en servidor web", "responsable": "Ana Pérez"}
    payload.update(overrides)
    headers = auth_headers(client, admin.email)
    return client.post("/cases", json=payload, headers=headers).json()


# --- sin token / token inválido -------------------------------------------


def test_get_cases_sin_token_es_401(client):
    assert client.get("/cases").status_code == 401


def test_post_cases_sin_token_es_401(client):
    r = client.post("/cases", json={"nombre": "X", "responsable": "Y"})
    assert r.status_code == 401


def test_get_case_con_token_invalido_es_401(client):
    r = client.get("/cases/1", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_delete_case_sin_token_es_401(client, admin):
    caso = crear_caso_como_admin(client, admin)
    r = client.delete(f"/cases/{caso['id']}")
    assert r.status_code == 401


def test_auditoria_sin_token_es_401(client, admin):
    caso = crear_caso_como_admin(client, admin)
    r = client.get(f"/cases/{caso['id']}/auditoria")
    assert r.status_code == 401


def test_evidences_sin_token_es_401(client, admin):
    caso = crear_caso_como_admin(client, admin)
    r = client.post(f"/cases/{caso['id']}/evidences", json={"tipo": "ip", "valor": "1.2.3.4"})
    assert r.status_code == 401


# --- analyst: operaciones normales permitidas -------------------------------


def test_analyst_puede_crear_y_listar_casos(client, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.post("/cases", json={"nombre": "Caso de analyst", "responsable": "Ana"}, headers=headers)
    assert r.status_code == 201, r.text

    r = client.get("/cases", headers=headers)
    assert r.status_code == 200


def test_analyst_puede_actualizar_caso(client, analyst):
    headers = auth_headers(client, analyst.email)
    caso = client.post("/cases", json={"nombre": "X", "responsable": "Y"}, headers=headers).json()
    r = client.put(f"/cases/{caso['id']}", json={"descripcion": "actualizado"}, headers=headers)
    assert r.status_code == 200


def test_analyst_puede_gestionar_evidencias(client, analyst):
    headers = auth_headers(client, analyst.email)
    caso = client.post("/cases", json={"nombre": "X", "responsable": "Y"}, headers=headers).json()

    r = client.post(f"/cases/{caso['id']}/evidences", json={"tipo": "ip", "valor": "1.2.3.4"}, headers=headers)
    assert r.status_code == 201, r.text
    evidencia = r.json()

    assert client.get(f"/cases/{caso['id']}/evidences", headers=headers).status_code == 200
    assert (
        client.delete(f"/cases/{caso['id']}/evidences/{evidencia['id']}", headers=headers).status_code
        == 204
    )


def test_analyst_puede_consultar_auditoria(client, analyst):
    headers = auth_headers(client, analyst.email)
    caso = client.post("/cases", json={"nombre": "X", "responsable": "Y"}, headers=headers).json()
    r = client.get(f"/cases/{caso['id']}/auditoria", headers=headers)
    assert r.status_code == 200


# --- analyst: operación administrativa prohibida (403) ----------------------


def test_delete_case_con_analyst_es_403(client, admin, analyst):
    caso = crear_caso_como_admin(client, admin)
    headers = auth_headers(client, analyst.email)
    r = client.delete(f"/cases/{caso['id']}", headers=headers)
    assert r.status_code == 403


# --- admin: operación administrativa permitida, mismo comportamiento actual -


def test_delete_case_con_admin_devuelve_204_y_borrado_logico(client, admin):
    caso = crear_caso_como_admin(client, admin)
    headers = auth_headers(client, admin.email)

    r = client.delete(f"/cases/{caso['id']}", headers=headers)
    assert r.status_code == 204

    r = client.get(f"/cases/{caso['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["eliminado"] is True


def test_admin_tambien_puede_las_operaciones_normales_de_analyst(client, admin):
    """admin = analyst + administrativas, no un permiso distinto."""
    headers = auth_headers(client, admin.email)
    r = client.post("/cases", json={"nombre": "X", "responsable": "Y"}, headers=headers)
    assert r.status_code == 201


# --- endpoints que deben seguir siendo públicos / funcionando igual --------


def test_health_sigue_siendo_publico(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_sigue_siendo_publico(client, admin):
    r = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    assert r.status_code == 200


def test_me_sigue_funcionando(client, admin):
    headers = auth_headers(client, admin.email)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == admin.email
