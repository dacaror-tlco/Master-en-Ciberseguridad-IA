"""
Guardar debe ser todo o nada, también con varios guardados a la vez.

Antes se confirmaba la base de datos y después se escribía la cadena de
integridad, sin exclusión entre peticiones: con 6 guardados simultáneos, 5
devolvían 500 pero TODAS las filas quedaban en `tracking_events` (240 filas
frente a 52 registros en la cadena). El perito veía error, reintentaba y
duplicaba eventos.
"""

import sqlite3
import threading
from datetime import datetime, timedelta, timezone

import pytest

from app.core.database import SessionLocal
from app.main import app
from app.modules.tracking import chain_integrity, service
from app.modules.tracking.models import Severidad
from app.modules.tracking.schemas import AnalyzePreviewItem, SaveEventsRequest
from .conftest import cliente
from .conftest import SharedCaseRow


@pytest.fixture
def case_id():
    with SessionLocal() as db:
        case = SharedCaseRow(nombre="Atomico", responsable="perito")
        db.add(case)
        db.commit()
        return case.id


def _eventos(n: int) -> list[dict]:
    base = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    return [
        {"hora": (base + timedelta(seconds=i)).isoformat(), "evento": f"cmd {i}", "severidad": "baja"}
        for i in range(n)
    ]


def _registros_en_cadena(case_id: int) -> int:
    conn = sqlite3.connect(chain_integrity._db_path_for_case(case_id))
    try:
        return conn.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
    finally:
        conn.close()


def test_guardados_concurrentes_no_fallan_ni_descuadran(case_id):
    cuerpo = {"case_id": case_id, "fuente_log": "a.log", "eventos": _eventos(40)}
    estados: list[int] = []

    def guardar():
        with cliente(raise_server_exceptions=False) as c:
            estados.append(c.post(f"/cases/{case_id}/tracking/events", json=cuerpo).status_code)

    hilos = [threading.Thread(target=guardar) for _ in range(6)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert estados == [200] * 6
    with cliente() as c:
        assert len(c.get(f"/cases/{case_id}/tracking/events?limit=1000").json()) == 240
        assert c.get(f"/cases/{case_id}/tracking/verify").json()["ok"] is True
    assert _registros_en_cadena(case_id) == 240


def test_si_falla_la_base_de_datos_la_cadena_se_deshace(case_id, monkeypatch):
    request = SaveEventsRequest(
        case_id=case_id,
        fuente_log="a.log",
        eventos=[AnalyzePreviewItem(hora=datetime(2026, 8, 10, tzinfo=timezone.utc), evento="x", severidad=Severidad.BAJA)],
    )
    with SessionLocal() as db:
        def commit_roto():
            raise RuntimeError("la base de datos se cayó")

        monkeypatch.setattr(db, "commit", commit_roto)
        with pytest.raises(RuntimeError):
            service.save_events(db, request)

    assert _registros_en_cadena(case_id) == 0
    with SessionLocal() as db:
        assert service.get_events_for_case(db, case_id) == []


def test_si_falla_la_cadena_no_se_guarda_nada_en_la_bd(case_id, monkeypatch):
    request = SaveEventsRequest(
        case_id=case_id,
        fuente_log="a.log",
        eventos=[AnalyzePreviewItem(hora=datetime(2026, 8, 10, tzinfo=timezone.utc), evento="x", severidad=Severidad.BAJA)],
    )

    def registro_roto(*_args, **_kwargs):
        raise OSError("disco lleno")

    monkeypatch.setattr(chain_integrity, "_registro_para", registro_roto)
    with SessionLocal() as db, pytest.raises(OSError):
        service.save_events(db, request)

    with SessionLocal() as db:
        assert service.get_events_for_case(db, case_id) == []


def test_la_hora_se_guarda_en_utc_y_a_segundos(case_id):
    madrid = timezone(timedelta(hours=2))
    request = SaveEventsRequest(
        case_id=case_id,
        fuente_log="a.log",
        eventos=[AnalyzePreviewItem(
            hora=datetime(2026, 8, 10, 16, 0, 5, 700000, tzinfo=madrid), evento="x", severidad=Severidad.BAJA,
        )],
    )
    with SessionLocal() as db:
        service.save_events(db, request)
        guardado = service.get_events_for_case(db, case_id)[0]
        verificacion = service.verify_integrity(db, case_id)

    assert guardado.hora.replace(tzinfo=None) == datetime(2026, 8, 10, 14, 0, 5)
    assert verificacion.ok is True


def test_eventos_del_mismo_segundo_salen_en_orden_de_guardado(case_id):
    hora = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc).isoformat()
    cuerpo = {
        "case_id": case_id,
        "fuente_log": "a.log",
        "eventos": [{"hora": hora, "evento": f"cmd {i}", "severidad": "baja"} for i in range(5)],
    }
    with cliente() as c:
        c.post(f"/cases/{case_id}/tracking/events", json=cuerpo)
        eventos = [e["evento"] for e in c.get(f"/cases/{case_id}/tracking/events").json()]
    assert eventos == [f"cmd {i}" for i in range(5)]
