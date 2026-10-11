"""
Optimizaciones que tienen que seguir funcionando: respuesta comprimida y sin
nulos, y el análisis fuera del bucle de eventos.
"""

import threading

import pytest

from app.main import app
from app.modules.tracking import routes
from .conftest import crear_caso


def _caso(client) -> int:
    return crear_caso("Rend", "perito")


def test_la_respuesta_del_analisis_va_comprimida_y_sin_nulos(client):
    case_id = _caso(client)
    log = "".join(f"2026-08-14 03:11:{i % 60:02d}  dir C:\\Users\\u{i}\n" for i in range(300))
    r = client.post(
        f"/cases/{case_id}/tracking/analyze",
        files={"file": ("a.log", log, "text/plain")},
        headers={"Accept-Encoding": "gzip"},
    )
    assert r.status_code == 200
    assert r.headers.get("content-encoding") == "gzip"
    assert "null" not in r.text


def test_el_analisis_no_bloquea_el_bucle_de_eventos(client, monkeypatch):
    """El análisis (CPU puro) se ejecuta en otro hilo, no en el del bucle de
    eventos: mientras dura, el resto de peticiones siguen respondiendo."""
    hilo_bucle: list[int] = []
    hilo_analisis: list[int] = []
    original_threadpool = routes.run_in_threadpool
    original_analizar = routes._analizar

    async def espiar_threadpool(funcion, *args):
        hilo_bucle.append(threading.get_ident())
        return await original_threadpool(funcion, *args)

    def espiar_analizar(*args):
        hilo_analisis.append(threading.get_ident())
        return original_analizar(*args)

    monkeypatch.setattr(routes, "run_in_threadpool", espiar_threadpool)
    monkeypatch.setattr(routes, "_analizar", espiar_analizar)
    case_id = _caso(client)
    r = client.post(f"/cases/{case_id}/tracking/analyze", files={"file": ("a.log", "2026-08-14 03:11:19  whoami\n")})

    assert r.status_code == 200
    assert hilo_bucle and hilo_analisis
    assert hilo_analisis[0] != hilo_bucle[0]
