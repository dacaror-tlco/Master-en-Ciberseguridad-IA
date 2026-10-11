"""
Identidad (Fase 1): /auth/login, /auth/me, gestión de usuarios y los
guardarraíles de auto-protección — ver propuesta de identidad y acceso,
secciones 13 y 14. Cases sigue sin protección todavía (eso es la Fase 3);
aquí solo se prueba el módulo `auth` en sí mismo.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.modules.auth.models import AuthAuditLog, AuthEvento, Rol, User
from tests.conftest import PASSWORD_PRUEBA, auth_headers


# --- login -------------------------------------------------------------


def test_login_correcto_devuelve_token_y_actualiza_ultimo_login(client, db_session, admin):
    assert admin.ultimo_login is None
    r = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == settings.JWT_EXPIRE_MINUTES * 60

    db_session.refresh(admin)
    assert admin.ultimo_login is not None

    eventos = db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.LOGIN_EXITOSO).all()
    assert len(eventos) == 1
    assert eventos[0].user_id == admin.id
    assert eventos[0].actor_user_id == admin.id


def test_login_email_inexistente_es_401_y_no_expone_si_el_email_existe(client, db_session):
    r = client.post("/auth/login", json={"email": "nadie@nexus.local", "password": "lo-que-sea"})
    assert r.status_code == 401

    evento = db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.LOGIN_FALLIDO).one()
    assert evento.user_id is None
    assert evento.actor_user_id is None
    assert evento.detalle == {"email_intentado": "nadie@nexus.local"}


def test_login_password_incorrecta_es_401(client, db_session, admin):
    r = client.post("/auth/login", json={"email": admin.email, "password": "incorrecta"})
    assert r.status_code == 401

    evento = db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.LOGIN_FALLIDO).one()
    assert evento.user_id == admin.id
    assert evento.actor_user_id == admin.id


def test_login_usuario_inactivo_es_401(client, db_session, admin):
    admin.activo = False
    db_session.commit()
    r = client.post("/auth/login", json={"email": admin.email, "password": PASSWORD_PRUEBA})
    assert r.status_code == 401


def test_ninguna_entrada_de_auditoria_contiene_la_contrasena(client, db_session, admin):
    client.post("/auth/login", json={"email": admin.email, "password": "otra-mala"})
    for evento in db_session.query(AuthAuditLog).all():
        detalle = str(evento.detalle or {})
        assert "otra-mala" not in detalle
        assert PASSWORD_PRUEBA not in detalle


# --- /auth/me ------------------------------------------------------------


def test_me_sin_token_es_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_con_token_invalido_es_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_me_con_token_expirado_es_401(client, admin):
    ahora = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(admin.id), "role": admin.rol.value, "iat": ahora - timedelta(hours=3), "exp": ahora - timedelta(hours=1)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_con_token_valido_devuelve_los_datos_del_usuario(client, admin):
    headers = auth_headers(client, admin.email)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == admin.id
    assert body["email"] == admin.email
    assert body["rol"] == "admin"


def test_usuario_desactivado_tras_emitir_el_token_pierde_el_acceso(client, db_session, admin):
    headers = auth_headers(client, admin.email)
    admin.activo = False
    db_session.commit()
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 401


# --- gestión de usuarios: autorización -----------------------------------


def test_crear_usuario_sin_token_es_401(client):
    r = client.post("/auth/users", json={"nombre": "X", "email": "x@nexus.local", "password": "12345678"})
    assert r.status_code == 401


def test_analyst_no_puede_crear_usuarios(client, analyst):
    headers = auth_headers(client, analyst.email)
    r = client.post(
        "/auth/users",
        json={"nombre": "X", "email": "x@nexus.local", "password": "12345678"},
        headers=headers,
    )
    assert r.status_code == 403


def test_analyst_no_puede_listar_usuarios(client, analyst):
    headers = auth_headers(client, analyst.email)
    assert client.get("/auth/users", headers=headers).status_code == 403


def test_analyst_no_puede_modificarse_a_si_mismo(client, analyst):
    """Ni siquiera sobre su propio id: el endpoint es admin-only, no hay
    ruta separada de "autoedición" que un analyst pueda alcanzar."""
    headers = auth_headers(client, analyst.email)
    r = client.put(f"/auth/users/{analyst.id}", json={"rol": "admin"}, headers=headers)
    assert r.status_code == 403


def test_admin_crea_usuario_y_queda_auditado(client, db_session, admin):
    headers = auth_headers(client, admin.email)
    r = client.post(
        "/auth/users",
        json={"nombre": "Nuevo Analyst", "email": "nuevo@nexus.local", "password": "12345678"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["rol"] == "analyst"
    assert body["activo"] is True

    evento = db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.USUARIO_CREADO).one()
    assert evento.user_id == body["id"]
    assert evento.actor_user_id == admin.id
    assert evento.detalle == {"email": "nuevo@nexus.local", "rol": "analyst"}


def test_crear_usuario_con_email_duplicado_es_409(client, admin):
    headers = auth_headers(client, admin.email)
    r = client.post(
        "/auth/users",
        json={"nombre": "Otro", "email": admin.email, "password": "12345678"},
        headers=headers,
    )
    assert r.status_code == 409


def test_admin_lista_usuarios(client, admin, analyst):
    headers = auth_headers(client, admin.email)
    r = client.get("/auth/users", headers=headers)
    assert r.status_code == 200
    emails = {u["email"] for u in r.json()}
    assert {admin.email, analyst.email} <= emails


# --- guardarraíles de PUT /auth/users/{id} -------------------------------


def test_cambio_de_rol_queda_auditado(client, db_session, admin, analyst):
    headers = auth_headers(client, admin.email)
    r = client.put(f"/auth/users/{analyst.id}", json={"rol": "admin"}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "admin"

    evento = db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.ROL_CAMBIADO).one()
    assert evento.user_id == analyst.id
    assert evento.actor_user_id == admin.id
    assert evento.detalle == {"de": "analyst", "a": "admin"}


def test_desactivar_y_reactivar_a_otro_usuario_queda_auditado(client, db_session, admin, analyst):
    headers = auth_headers(client, admin.email)

    r = client.put(f"/auth/users/{analyst.id}", json={"activo": False}, headers=headers)
    assert r.status_code == 200
    assert r.json()["activo"] is False
    assert db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.USUARIO_DESACTIVADO).count() == 1

    r = client.put(f"/auth/users/{analyst.id}", json={"activo": True}, headers=headers)
    assert r.status_code == 200
    assert r.json()["activo"] is True
    assert db_session.query(AuthAuditLog).filter_by(evento=AuthEvento.USUARIO_REACTIVADO).count() == 1


def test_admin_no_puede_desactivarse_a_si_mismo_aunque_haya_otros_admins(client, db_session, admin):
    _crear_segundo_admin(db_session)
    headers = auth_headers(client, admin.email)
    r = client.put(f"/auth/users/{admin.id}", json={"activo": False}, headers=headers)
    assert r.status_code == 409


def test_ultimo_admin_no_puede_quitarse_el_rol(client, admin):
    headers = auth_headers(client, admin.email)
    r = client.put(f"/auth/users/{admin.id}", json={"rol": "analyst"}, headers=headers)
    assert r.status_code == 409


def test_admin_si_puede_degradarse_si_quedan_otros_admins(client, db_session, admin):
    _crear_segundo_admin(db_session)
    headers = auth_headers(client, admin.email)
    r = client.put(f"/auth/users/{admin.id}", json={"rol": "analyst"}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "analyst"


def test_no_se_puede_desactivar_al_ultimo_admin_desde_otra_cuenta(client, db_session, admin):
    """No solo autoprotección: tampoco se puede dejar el sistema sin
    admins desactivando/degradando a OTRO admin que resulta ser el
    último."""
    segundo = _crear_segundo_admin(db_session)
    headers = auth_headers(client, admin.email)
    r = client.put(f"/auth/users/{segundo.id}", json={"activo": False}, headers=headers)
    assert r.status_code == 200  # todavía queda `admin` activo: se permite

    r = client.put(f"/auth/users/{admin.id}", json={"activo": False}, headers=headers)
    assert r.status_code == 409  # ahora `admin` (self) es el único admin activo


def test_actualizar_usuario_inexistente_es_404(client, admin):
    headers = auth_headers(client, admin.email)
    r = client.put("/auth/users/999999", json={"nombre": "X"}, headers=headers)
    assert r.status_code == 404


def _crear_segundo_admin(db_session) -> User:
    from tests.conftest import _crear_usuario

    return _crear_usuario(db_session, nombre="Admin Dos", email="admin2@nexus.local", rol=Rol.ADMIN)
