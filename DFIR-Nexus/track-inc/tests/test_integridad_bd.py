"""
La verificación de integridad debe comparar la cadena local con lo que hay
DE VERDAD en `tracking_events`. Antes solo validaba la cadena, y respondía
"Cadena íntegra" aunque se hubieran editado o borrado eventos en la base de
datos, que es precisamente lo que tiene que detectar.
"""

import re

import pytest
from sqlalchemy import text

from app.core.database import engine
from app.main import app
from app.modules.tracking import chain_integrity
from .conftest import crear_caso

LOG = (
    "2026-08-10 14:32:05 powershell.exe -EncodedCommand SQBFAFgA\n"
    "2026-08-10 14:32:11 net user hacker P@ssw0rd123! /add\n"
)


def _caso_con_eventos(client) -> int:
    case_id = crear_caso("Integridad", "perito")
    preview = client.post(
        f"/cases/{case_id}/tracking/analyze", files={"file": ("i.log", LOG, "text/plain")}
    ).json()["eventos"]
    r = client.post(
        f"/cases/{case_id}/tracking/events",
        json={"case_id": case_id, "fuente_log": "i.log", "eventos": preview},
    )
    assert r.status_code == 200
    return case_id


def _verificar(client, case_id):
    r = client.get(f"/cases/{case_id}/tracking/verify")
    assert r.status_code == 200
    return r.json()


def test_intacto(client):
    case_id = _caso_con_eventos(client)
    body = _verificar(client, case_id)
    assert body["ok"] is True
    assert body["problemas"] == []


def test_detecta_evento_modificado_en_la_bd(client):
    case_id = _caso_con_eventos(client)
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE tracking_events SET evento = 'hostname', severidad = 'baja' "
            "WHERE id = (SELECT MIN(id) FROM tracking_events WHERE case_id = :c)"
        ), {"c": case_id})

    body = _verificar(client, case_id)
    assert body["ok"] is False
    assert len(body["problemas"]) == 1
    assert "modificado" in body["problemas"][0]
    assert "evento" in body["problemas"][0] and "severidad" in body["problemas"][0]


def test_detecta_evento_borrado_de_la_bd(client):
    case_id = _caso_con_eventos(client)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tracking_events WHERE case_id = :c"), {"c": case_id})

    body = _verificar(client, case_id)
    assert body["ok"] is False
    assert len(body["problemas"]) == 2
    assert all("borrado" in p for p in body["problemas"])


def test_detecta_evento_insertado_por_fuera(client):
    case_id = _caso_con_eventos(client)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO tracking_events (case_id, hora, evento, severidad) "
            "VALUES (:c, '2026-08-10 14:40:00', 'evento falso', 'baja')"
        ), {"c": case_id})

    body = _verificar(client, case_id)
    assert body["ok"] is False
    assert any("insertado por fuera" in p for p in body["problemas"])


def test_eventos_en_bd_sin_fichero_de_cadena_no_es_integro(client):
    case_id = _caso_con_eventos(client)
    chain_integrity._db_path_for_case(case_id).unlink()

    body = _verificar(client, case_id)
    assert body["ok"] is False
    # Lo habitual es un despliegue sin volumen para la cadena, no un ataque:
    # se dice así, en vez de listar cada evento como "insertado por fuera".
    assert "No se encuentra la cadena" in body["mensaje"]
    assert "volumen persistente" in body["mensaje"]
    assert body["problemas"] == []


def test_caso_inexistente_da_404(client):
    assert client.get("/cases/424242/tracking/verify").status_code == 404


def test_la_cadena_vive_en_una_ruta_absoluta():
    """Relativa al directorio de arranque, se perdía al arrancar desde otra
    carpeta y pytest borraba las cadenas reales."""
    assert chain_integrity.CHAIN_STORAGE_DIR.is_absolute()


def test_manipular_la_cadena_no_expone_hashes(client):
    case_id = _caso_con_eventos(client)
    import sqlite3
    conn = sqlite3.connect(chain_integrity._db_path_for_case(case_id))
    conn.execute("UPDATE evidence_records SET hash = ? WHERE seq = 1", ("f" * 64,))
    conn.commit()
    conn.close()

    body = _verificar(client, case_id)
    assert body["ok"] is False
    assert not re.search(r"[0-9a-f]{64}", body["mensaje"])
