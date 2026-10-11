import pytest

from app.main import app
from .conftest import crear_caso

SAMPLE_LOG = (
    "2026-08-10 14:32:05 powershell.exe -EncodedCommand SQBFAFgA\n"
    "2026-08-10 14:32:11 net user hacker P@ssw0rd123! /add\n"
)


def _create_case(client, nombre="Caso E2E", responsable="perito") -> int:
    """El caso se inserta directamente, como en `development`: Tracking no
    expone ninguna ruta para crear casos (son del Módulo 1)."""
    return crear_caso(nombre, responsable)


def test_full_flow_analyze_save_list_verify(client):
    case_id = _create_case(client)

    files = {"file": ("incidente.log", SAMPLE_LOG, "text/plain")}
    r = client.post(f"/cases/{case_id}/tracking/analyze", files=files)
    assert r.status_code == 200
    preview = r.json()["eventos"]
    assert len(preview) == 2

    save_payload = {"case_id": case_id, "fuente_log": "incidente.log", "eventos": preview}
    r = client.post(f"/cases/{case_id}/tracking/events", json=save_payload)
    assert r.status_code == 200
    assert r.json()["guardados"] == 2

    r = client.get(f"/cases/{case_id}/tracking/events")
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get(f"/cases/{case_id}/tracking/verify")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_response_schema_never_leaks_hash_fields(client):
    """Comprobación explícita de la decisión de diseño: nada de hash,
    prev_hash, seq, etc. debe aparecer en las respuestas de la API."""
    case_id = _create_case(client)
    files = {"file": ("incidente.log", SAMPLE_LOG, "text/plain")}
    preview = client.post(f"/cases/{case_id}/tracking/analyze", files=files).json()["eventos"]
    save_payload = {"case_id": case_id, "fuente_log": "incidente.log", "eventos": preview}
    r = client.post(f"/cases/{case_id}/tracking/events", json=save_payload)

    body_text = r.text.lower()
    for forbidden in ["hash", "prev_hash", "chain", "seq"]:
        assert forbidden not in body_text


def test_saved_events_keep_rule_and_inferred_time(client):
    """`tracking_events` no tiene columnas para la regla ni para saber si la
    hora fue inferida; se conservan en la cadena local y vuelven al listar."""
    case_id = _create_case(client)
    log = "2026-08-10 14:32:05 net user hacker P@ss /add\nwhoami\n"
    files = {"file": ("incidente.log", log, "text/plain")}
    preview = client.post(f"/cases/{case_id}/tracking/analyze", files=files).json()["eventos"]
    client.post(
        f"/cases/{case_id}/tracking/events",
        json={"case_id": case_id, "fuente_log": "incidente.log", "eventos": preview},
    )

    eventos = client.get(f"/cases/{case_id}/tracking/events").json()
    assert eventos[0]["regla"] == "cuenta_o_grupo_modificado"
    assert eventos[0]["hora_inferida"] is False
    assert eventos[1]["regla"] is None
    assert eventos[1]["hora_inferida"] is True
    assert eventos[1]["hora"] == eventos[0]["hora"]


def test_events_endpoint_404_for_nonexistent_case(client):
    r = client.get("/cases/99999/tracking/events")
    assert r.status_code == 404


def test_save_events_404_for_nonexistent_case(client):
    payload = {"case_id": 99999, "fuente_log": "x.log", "eventos": []}
    r = client.post("/cases/99999/tracking/events", json=payload)
    assert r.status_code == 404


def test_save_events_400_when_case_id_mismatch(client):
    case_id = _create_case(client)
    payload = {"case_id": 99999, "fuente_log": "x.log", "eventos": []}  # no coincide con la URL
    r = client.post(f"/cases/{case_id}/tracking/events", json=payload)
    assert r.status_code == 400


def test_analyze_rejects_non_utf8_file(client):
    case_id = _create_case(client)
    files = {"file": ("bin.log", b"\xff\xfe\x00\x01binario", "application/octet-stream")}
    r = client.post(f"/cases/{case_id}/tracking/analyze", files=files)
    assert r.status_code == 400


def test_tampering_tracking_event_after_save_is_detected_on_verify(client):
    """Test de integración clave: si alguien edita directamente una fila
    de tracking_events ya guardada (sin pasar por la API), la
    verificación de integridad interna debe detectarlo."""
    case_id = _create_case(client)
    files = {"file": ("incidente.log", SAMPLE_LOG, "text/plain")}
    preview = client.post(f"/cases/{case_id}/tracking/analyze", files=files).json()["eventos"]
    save_payload = {"case_id": case_id, "fuente_log": "incidente.log", "eventos": preview}
    client.post(f"/cases/{case_id}/tracking/events", json=save_payload)

    # antes de manipular, la cadena está íntegra
    r = client.get(f"/cases/{case_id}/tracking/verify")
    assert r.json()["ok"] is True

    # manipulamos directamente el store local de la cadena (simulando que
    # alguien accede al fichero sin pasar por la API)
    from app.modules.tracking.chain_integrity import _db_path_for_case
    from agent.evidence.store import EvidenceStore

    store = EvidenceStore(_db_path_for_case(case_id))
    records = store.get_all()
    store.close()

    import sqlite3
    conn = sqlite3.connect(_db_path_for_case(case_id))
    conn.execute("UPDATE evidence_records SET event_json = ? WHERE seq = 0",
                 (records[0].event.model_copy(update={"event_type": "manipulado"}).model_dump_json(),))
    conn.commit()
    conn.close()

    r = client.get(f"/cases/{case_id}/tracking/verify")
    assert r.json()["ok"] is False
    assert "comprometida" in r.json()["mensaje"]
