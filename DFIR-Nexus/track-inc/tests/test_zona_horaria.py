"""
La hora de un evento no debe cambiar entre la vista previa y lo guardado, y
el perito debe poder decir en qué zona horaria está escrito el log.

Antes la vista previa devolvía `03:11:19Z` y lo guardado `03:11:19` sin zona:
el navegador leía lo segundo como hora local, y en España la misma línea
salía a las 05:11 en la vista previa y a las 03:11 en "Eventos guardados".
"""

from datetime import timedelta, timezone

import pytest

from app.main import app
from app.modules.tracking.log_parser import parse_log_text
from app.modules.tracking.tiempo import parsear_zona
from .conftest import crear_caso

LOG = "2026-08-14 03:11:19  whoami\n"


def _caso(client) -> int:
    return crear_caso("Zona", "perito")


def test_la_hora_guardada_sale_en_utc_igual_que_la_vista_previa(client):
    case_id = _caso(client)
    preview = client.post(
        f"/cases/{case_id}/tracking/analyze", files={"file": ("a.log", LOG, "text/plain")}
    ).json()["eventos"]
    guardado = client.post(
        f"/cases/{case_id}/tracking/events",
        json={"case_id": case_id, "fuente_log": "a.log", "eventos": preview},
    ).json()["tracking_events"]
    listado = client.get(f"/cases/{case_id}/tracking/events").json()

    assert preview[0]["hora"] == "2026-08-14T03:11:19Z"
    assert guardado[0]["hora"] == "2026-08-14T03:11:19Z"
    assert listado[0]["hora"] == "2026-08-14T03:11:19Z"


def test_zona_horaria_del_log_se_convierte_a_utc(client):
    case_id = _caso(client)
    r = client.post(
        f"/cases/{case_id}/tracking/analyze",
        files={"file": ("a.log", LOG, "text/plain")},
        data={"zona_horaria": "+02:00"},
    )
    assert r.status_code == 200
    assert r.json()["eventos"][0]["hora"] == "2026-08-14T01:11:19Z"


def test_zona_horaria_invalida_da_400(client):
    case_id = _caso(client)
    r = client.post(
        f"/cases/{case_id}/tracking/analyze",
        files={"file": ("a.log", LOG, "text/plain")},
        data={"zona_horaria": "Marte/Olympus"},
    )
    assert r.status_code == 400
    assert "Zona horaria" in r.json()["detail"]


@pytest.mark.parametrize(
    ("texto", "desplazamiento"),
    [("UTC", 0), (None, 0), ("+02:00", 120), ("-05:30", -330), ("+14:00", 840)],
)
def test_parsear_zona(texto, desplazamiento):
    assert parsear_zona(texto).utcoffset(None) == timedelta(minutes=desplazamiento)


@pytest.mark.parametrize("texto", ["+15:00", "02:00", "Europe/Madrid", "+2"])
def test_parsear_zona_rechaza_formatos_no_validos(texto):
    with pytest.raises(ValueError):
        parsear_zona(texto)


def test_parser_interpreta_la_hora_en_la_zona_indicada():
    evento = parse_log_text(LOG, "a.log", zona=timezone(timedelta(hours=-5)))[0]
    assert evento.timestamp.isoformat() == "2026-08-14T08:11:19+00:00"
