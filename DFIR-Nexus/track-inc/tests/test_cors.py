"""
Solo el frontend propio puede llamar a la API desde otro origen.

Con `allow_origins=["*"]`, cualquier web abierta en el navegador del perito
podía escribir en `tracking_events` a través de su backend local.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _preflight(origen: str):
    return client.options(
        "/cases/1/tracking/events",
        headers={
            "Origin": origen,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_origen_ajeno_no_recibe_permiso():
    r = _preflight("https://sitio-malicioso.example")
    assert r.headers.get("access-control-allow-origin") is None


def test_frontend_en_modo_desarrollo_si_puede():
    for origen in ("http://localhost:5173", "http://127.0.0.1:5173"):
        r = _preflight(origen)
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == origen
