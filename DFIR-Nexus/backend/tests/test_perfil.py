"""
Pantalla de Perfil: PUT /auth/me/password y GET /auth/me/actividad. El
usuario objetivo es siempre el que resuelve get_current_user a partir del
JWT — ningún endpoint de este fichero acepta un user_id del cliente.
"""
from app.modules.auth.models import AuthAuditLog, AuthEvento
from app.modules.auth.security import verify_password
from tests.conftest import PASSWORD_PRUEBA, auth_headers

NUEVA_PASSWORD = "una-password-nueva-valida-123"


def _payload(actual=PASSWORD_PRUEBA, nueva=NUEVA_PASSWORD, confirmacion=None):
    return {
        "contrasena_actual": actual,
        "contrasena_nueva": nueva,
        "confirmacion_contrasena_nueva": confirmacion if confirmacion is not None else nueva,
    }


# --- cambio de contraseña ---------------------------------------------


def test_usuario_autenticado_puede_cambiar_su_contrasena(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.put("/auth/me/password", json=_payload(), headers=headers)
    assert r.status_code == 204, r.text

    db_session.refresh(analyst)
    # login con la contraseña VIEJA ya no funciona
    r = client.post("/auth/login", json={"email": analyst.email, "password": PASSWORD_PRUEBA})
    assert r.status_code == 401
    # login con la NUEVA sí
    r = client.post("/auth/login", json={"email": analyst.email, "password": NUEVA_PASSWORD})
    assert r.status_code == 200


def test_nueva_password_queda_almacenada_con_argon2id(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    client.put("/auth/me/password", json=_payload(), headers=headers)

    db_session.refresh(analyst)
    assert analyst.password_hash.startswith("$argon2id$")
    assert verify_password(NUEVA_PASSWORD, analyst.password_hash)
    assert not verify_password(PASSWORD_PRUEBA, analyst.password_hash)


def test_contrasena_actual_incorrecta_es_401(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.put(
        "/auth/me/password", json=_payload(actual="esto-no-es-la-actual"), headers=headers
    )
    assert r.status_code == 401

    db_session.refresh(analyst)
    assert verify_password(PASSWORD_PRUEBA, analyst.password_hash)  # sin cambios


def test_confirmacion_no_coincide_es_422(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.put(
        "/auth/me/password",
        json=_payload(nueva=NUEVA_PASSWORD, confirmacion="otra-cosa-distinta-123"),
        headers=headers,
    )
    assert r.status_code == 422

    db_session.refresh(analyst)
    assert verify_password(PASSWORD_PRUEBA, analyst.password_hash)  # sin cambios


def test_password_nueva_demasiado_corta_es_422(client, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.put("/auth/me/password", json=_payload(nueva="corta", confirmacion="corta"), headers=headers)
    assert r.status_code == 422


def test_cambiar_password_sin_token_es_401(client):
    r = client.put("/auth/me/password", json=_payload())
    assert r.status_code == 401


def test_no_se_puede_cambiar_la_password_de_otro_usuario(client, db_session, analyst, admin):
    """No existe ningún user_id en el body: aunque un cliente intente
    inyectar uno para apuntar a otra cuenta, se ignora — el objetivo lo
    decide siempre el JWT (aquí, el de `analyst`), nunca el body."""
    headers = auth_headers(client, analyst.email)
    payload = _payload()
    payload["user_id"] = admin.id  # intento de manipulación
    r = client.put("/auth/me/password", json=payload, headers=headers)
    assert r.status_code == 204, r.text

    db_session.refresh(admin)
    db_session.refresh(analyst)
    # admin.password_hash NUNCA se tocó
    assert verify_password(PASSWORD_PRUEBA, admin.password_hash)
    # el afectado es analyst, el dueño real del JWT
    assert verify_password(NUEVA_PASSWORD, analyst.password_hash)


def test_cambio_de_password_queda_auditado_como_evento_propio(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    client.put("/auth/me/password", json=_payload(), headers=headers)

    evento = (
        db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.CONTRASENA_CAMBIADA).one()
    )
    assert evento.user_id == analyst.id
    assert evento.actor_user_id == analyst.id


def test_respuesta_del_cambio_de_password_no_contiene_secretos(client, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.put("/auth/me/password", json=_payload(), headers=headers)
    assert r.status_code == 204
    assert r.text == ""  # 204 No Content: no hay body, ni hash ni contraseña que filtrar


def test_ninguna_entrada_de_auditoria_contiene_la_contrasena(client, db_session, analyst):
    headers = auth_headers(client, analyst.email)
    client.put("/auth/me/password", json=_payload(), headers=headers)

    for evento in db_session.query(AuthAuditLog).all():
        detalle = str(evento.detalle or {})
        assert PASSWORD_PRUEBA not in detalle
        assert NUEVA_PASSWORD not in detalle


# --- actividad propia ---------------------------------------------------


def test_actividad_solo_devuelve_eventos_del_usuario_autenticado(client, admin, analyst):
    # genera actividad de ambos usuarios
    auth_headers(client, admin.email)  # login de admin -> login_exitoso para admin
    analyst_headers = auth_headers(client, analyst.email)  # login de analyst

    r = client.get("/auth/me/actividad", headers=analyst_headers)
    assert r.status_code == 200
    eventos = r.json()
    assert len(eventos) >= 1
    assert all(e["user_id"] == analyst.id for e in eventos)
    assert all(e["user_id"] != admin.id for e in eventos)


def test_actividad_incluye_login_exitoso_y_cambio_de_password(client, analyst):
    headers = auth_headers(client, analyst.email)  # ya genera un login_exitoso
    client.put("/auth/me/password", json=_payload(), headers=headers)

    r = client.get("/auth/me/actividad", headers=headers)
    tipos = [e["evento"] for e in r.json()]
    assert "login_exitoso" in tipos
    assert "contrasena_cambiada" in tipos


def test_actividad_sin_token_es_401(client):
    assert client.get("/auth/me/actividad").status_code == 401


def test_actividad_no_expone_contrasenas_ni_hash(client, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.get("/auth/me/actividad", headers=headers)
    cuerpo = r.text.lower()
    assert "password" not in cuerpo
    assert "$argon2id$" not in cuerpo
    assert PASSWORD_PRUEBA not in r.text
