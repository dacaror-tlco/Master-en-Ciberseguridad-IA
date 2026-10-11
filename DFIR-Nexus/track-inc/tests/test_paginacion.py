"""
El listado de eventos se pagina con skip/limit, el mismo patrón que Casos y
OSINT. Antes devolvía todos los eventos del caso sin límite.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.database import SessionLocal
from app.main import app
from app.modules.tracking import service
from .conftest import SharedCaseRow, cliente

TOTAL = 12


@pytest.fixture
def case_id():
    with SessionLocal() as db:
        caso = SharedCaseRow(nombre="Paginacion", responsable="perito")
        db.add(caso)
        db.commit()
        cid = caso.id
    base = datetime(2026, 8, 14, 3, 0, tzinfo=timezone.utc)
    with cliente() as c:
        c.post(
            f"/cases/{cid}/tracking/events",
            json={
                "case_id": cid,
                "fuente_log": "a.log",
                "eventos": [
                    {"hora": (base + timedelta(seconds=i)).isoformat(), "evento": f"cmd {i}", "severidad": "baja"}
                    for i in range(TOTAL)
                ],
            },
        )
    return cid


def _eventos(client, case_id, query=""):
    r = client.get(f"/cases/{case_id}/tracking/events{query}")
    assert r.status_code == 200
    return [e["evento"] for e in r.json()]


def test_pagina_con_skip_y_limit(client, case_id):
    assert _eventos(client, case_id, "?limit=5") == [f"cmd {i}" for i in range(5)]
    assert _eventos(client, case_id, "?skip=5&limit=5") == [f"cmd {i}" for i in range(5, 10)]
    assert _eventos(client, case_id, "?skip=10&limit=5") == [f"cmd {i}" for i in range(10, TOTAL)]
    assert _eventos(client, case_id, "?skip=100") == []


def test_sin_parametros_devuelve_la_primera_pagina(client, case_id):
    assert len(_eventos(client, case_id)) == TOTAL  # menos de 100, caben todos


@pytest.mark.parametrize("query", ["?skip=-1", "?limit=0", "?limit=1001"])
def test_parametros_fuera_de_rango_dan_422(client, case_id, query):
    assert client.get(f"/cases/{case_id}/tracking/events{query}").status_code == 422


def test_la_verificacion_de_integridad_mira_todos_los_eventos(client, case_id, monkeypatch):
    """La paginación es de la API: verificar integridad necesita el caso
    entero, no una página."""
    with SessionLocal() as db:
        assert len(service.get_events_for_case(db, case_id)) == TOTAL
    body = client.get(f"/cases/{case_id}/tracking/verify").json()
    assert body["ok"] is True
    assert str(TOTAL) in body["mensaje"]
