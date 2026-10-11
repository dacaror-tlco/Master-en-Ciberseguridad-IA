"""
Validaciones de la API: duplicados, longitudes de columna, casos inexistentes
o eliminados, tamaño del fichero y rutas que no existen.
"""

import hashlib

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.main import app
from app.modules.tracking import repository
from .conftest import crear_caso

LOG = "2026-08-14 03:11:19  whoami\n2026-08-14 03:11:25  net user hacker P@ss /add\n"


def _caso(client) -> int:
    return crear_caso("Val", "perito")


def _analizar(client, case_id, contenido=LOG, nombre="i.log"):
    return client.post(f"/cases/{case_id}/tracking/analyze", files={"file": (nombre, contenido, "text/plain")})


def _guardar(client, case_id, analisis, **extra):
    cuerpo = {"case_id": case_id, "fuente_log": "i.log", "eventos": analisis["eventos"],
              "sha256_log": analisis["sha256_log"], **extra}
    return client.post(f"/cases/{case_id}/tracking/events", json=cuerpo)


# --- duplicados -------------------------------------------------------------

def test_analisis_devuelve_el_sha256_del_fichero(client):
    case_id = _caso(client)
    analisis = _analizar(client, case_id).json()
    assert analisis["sha256_log"] == hashlib.sha256(LOG.encode()).hexdigest()
    assert analisis["eventos_ya_guardados"] == 0


def test_guardar_dos_veces_el_mismo_log_da_409_y_avisa_al_analizar(client):
    case_id = _caso(client)
    analisis = _analizar(client, case_id).json()
    assert _guardar(client, case_id, analisis).status_code == 200

    assert _analizar(client, case_id).json()["eventos_ya_guardados"] == 2
    r = _guardar(client, case_id, analisis)
    assert r.status_code == 409
    assert "ya se guardó" in r.json()["detail"]
    assert len(client.get(f"/cases/{case_id}/tracking/events").json()) == 2


def test_forzar_permite_guardarlo_otra_vez(client):
    case_id = _caso(client)
    analisis = _analizar(client, case_id).json()
    _guardar(client, case_id, analisis)
    assert _guardar(client, case_id, analisis, forzar=True).status_code == 200
    assert len(client.get(f"/cases/{case_id}/tracking/events").json()) == 4


def test_el_mismo_log_en_otro_caso_no_es_duplicado(client):
    uno, otro = _caso(client), _caso(client)
    _guardar(client, uno, _analizar(client, uno).json())
    analisis = _analizar(client, otro).json()
    assert analisis["eventos_ya_guardados"] == 0
    assert _guardar(client, otro, analisis).status_code == 200


# --- longitudes de columna --------------------------------------------------

def test_fuente_log_de_mas_de_100_caracteres_da_422(client):
    case_id = _caso(client)
    analisis = _analizar(client, case_id).json()
    cuerpo = {"case_id": case_id, "fuente_log": "f" * 101, "eventos": analisis["eventos"]}
    assert client.post(f"/cases/{case_id}/tracking/events", json=cuerpo).status_code == 422


def test_usuario_de_mas_de_100_caracteres_da_422(client):
    case_id = _caso(client)
    evento = {"hora": "2026-08-14T03:11:19Z", "evento": "x", "severidad": "baja", "usuario_detectado": "u" * 101}
    cuerpo = {"case_id": case_id, "fuente_log": "i.log", "eventos": [evento]}
    assert client.post(f"/cases/{case_id}/tracking/events", json=cuerpo).status_code == 422


def test_evento_que_no_cabe_en_text_da_422(client):
    case_id = _caso(client)
    evento = {"hora": "2026-08-14T03:11:19Z", "evento": "ñ" * 40000, "severidad": "baja"}  # 80.000 bytes
    cuerpo = {"case_id": case_id, "fuente_log": "i.log", "eventos": [evento]}
    assert client.post(f"/cases/{case_id}/tracking/events", json=cuerpo).status_code == 422


def test_linea_con_solo_la_hora_no_produce_un_evento_vacio(client):
    case_id = _caso(client)
    r = _analizar(client, case_id, "2026-08-14 03:11:19\n")
    assert r.status_code == 200
    assert r.json()["eventos"][0]["evento"] == "2026-08-14 03:11:19"


# --- casos inexistentes o eliminados ------------------------------------------

def test_analizar_sobre_un_caso_inexistente_da_404(client):
    assert _analizar(client, 99999).status_code == 404


def _caso_con_un_evento(client) -> int:
    case_id = _caso(client)
    assert _guardar(client, case_id, _analizar(client, case_id).json()).status_code == 200
    return case_id


def test_un_caso_eliminado_se_consulta_pero_no_admite_eventos(client):
    """Mismo criterio que Casos: el borrado lógico (`eliminado`) impide
    escribir, pero lo ya registrado se sigue pudiendo consultar."""
    case_id = _caso_con_un_evento(client)
    with engine.begin() as conn:
        conn.execute(text("UPDATE cases SET eliminado = 1 WHERE id = :id"), {"id": case_id})

    r = _analizar(client, case_id)
    assert r.status_code == 409
    assert r.json()["detail"] == "El caso está eliminado"
    evento = {"hora": "2026-08-14T03:11:19Z", "evento": "x", "severidad": "baja"}
    r = client.post(f"/cases/{case_id}/tracking/events", json={"case_id": case_id, "fuente_log": "i.log", "eventos": [evento]})
    assert r.status_code == 409

    assert len(client.get(f"/cases/{case_id}/tracking/events").json()) == 2
    assert client.get(f"/cases/{case_id}/tracking/verify").json()["ok"] is True


def test_un_caso_archivado_no_admite_eventos(client):
    case_id = crear_caso("Archivado", "perito", estado="archivado")
    r = _analizar(client, case_id)
    assert r.status_code == 409
    assert "archivado" in r.json()["detail"]


def test_el_selector_de_casos_no_ofrece_los_eliminados(client):
    activo = crear_caso("Activo", "perito")
    crear_caso("Borrado", "perito", eliminado=True)
    casos = client.get("/cases-lookup").json()
    assert [c["id"] for c in casos] == [activo]
    assert set(casos[0]) == {"id", "nombre", "estado"}


def test_sin_columna_eliminado_todo_caso_existente_esta_activo():
    """La tabla `cases` de pruebas local (migración 0001) no tiene `eliminado`:
    Tracking debe funcionar igual, sin romperse."""
    case_id = crear_caso("Sin columna", "perito")
    with SessionLocal() as db:
        repository._columnas_cases[str(db.get_bind().url)] = {"id", "nombre", "estado", "responsable"}
        try:
            estado = repository.estado_caso(db, case_id)
            opciones = repository.list_case_options(db)
        finally:
            repository._columnas_cases.clear()
    assert estado.existe and not estado.eliminado
    assert [o["id"] for o in opciones] == [case_id]


# --- tamaño y rutas -----------------------------------------------------------

def test_fichero_demasiado_grande_da_413(client, monkeypatch):
    monkeypatch.setenv("TRACKING_MAX_LOG_MB", "0.001")  # ~1 KB
    case_id = _caso(client)
    assert _analizar(client, case_id, "2026-08-14 03:11:19  whoami\n" * 100).status_code == 413


def test_ruta_de_api_inexistente_da_404_json(client):
    r = client.get("/cases/1/tracking/noexiste")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
