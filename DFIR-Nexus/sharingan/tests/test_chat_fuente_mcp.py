"""
El asistente leyendo el expediente a través del servidor MCP.

Sin simular el cliente MCP: cada test lanza el `mcp-server/` real por stdio,
igual que en producción, y lo apunta a un backend HTTP falso levantado aquí
que sirve las seis lecturas y apunta qué le piden y con qué token. Así se
prueba la cadena completa: proceso, transporte, herramientas, JWT y armado
del contexto.
"""
from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from app.core.config import settings
from app.modules.chat import context as contexto_mod
from app.modules.chat import fuente_mcp, service

MCP_DIR = Path(__file__).resolve().parents[2] / "mcp-server"
TOKEN = "jwt-del-analista-que-pregunta"

CASO = {
    "id": 19, "nombre": "Malspam QakBot", "estado": "en_progreso", "responsable": "Pablo",
    "descripcion": "Caso de prueba", "fecha_creacion": "2026-09-26T10:10:14",
}
RUTAS = {
    "/cases/19": CASO,
    # Desordenadas a propósito: la numeración de las citas no puede depender
    # del orden en que responda la API.
    "/cases/19/evidences": [
        {"id": 21, "tipo": "ip", "valor": "50.16.16.211", "observaciones": None,
         "fecha_subida": "2026-09-26T10:10:18"},
        {"id": 20, "tipo": "url", "valor": "https://metrics.agoxpathbet.one/Fabrics.a3x",
         "observaciones": "dropper", "fecha_subida": "2026-09-26T10:10:17"},
    ],
    "/osint-findings": [
        {"id": 158, "case_type": "ip", "source_table": "osint_ip_cases", "source_id": 3,
         "case_id": 19, "subject_type": "ip", "subject_value": "50.16.16.211",
         "risk_score": 20, "risk_level": "low", "headline": "C2 QakBot", "flag_count": 1,
         "analyzed_at": "2026-09-26T11:00:00", "created_at": "2026-09-26T11:00:00"},
    ],
    "/cases/19/tracking/events": [
        {"id": 7, "case_id": 19, "hora": "2026-09-26T09:15:40+00:00", "evento": "Failed password",
         "severidad": "alta", "fuente_log": "auth.log", "usuario_detectado": "admin",
         "regla": None, "hora_inferida": False},
    ],
    "/timeline/cases/19": [
        {"id": 90, "case_id": 19, "fecha_hora": "2026-09-26T09:15:40",
         "descripcion": "Intento de acceso SSH", "origen_modulo": "tracking", "origen_id": 7,
         "orden": 1},
    ],
    "/cases/19/reports": [
        {"id": 8, "case_id": 19, "version": 2, "fecha_generacion": "2026-09-26T15:58:37",
         "generado_por": "Pablo Pérez", "resumen_ia": "…", "archivo_pdf": "x", "notas": None,
         "huellas": {}, "opciones": None},
    ],
}


class _Backend(BaseHTTPRequestHandler):
    peticiones: list[tuple[str, str]] = []
    fallar = False

    def do_GET(self):  # noqa: N802 (nombre impuesto por http.server)
        ruta = self.path.split("?")[0]
        type(self).peticiones.append((self.path, self.headers.get("Authorization", "")))
        if type(self).fallar:
            return self._responder(500, {"detail": "caído"})
        if ruta in RUTAS:
            return self._responder(200, RUTAS[ruta])
        return self._responder(404, {"detail": "no existe"})

    def _responder(self, codigo: int, cuerpo) -> None:
        datos = json.dumps(cuerpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args):
        pass


@pytest.fixture
def backend(monkeypatch):
    _Backend.peticiones = []
    _Backend.fallar = False
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), _Backend)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{servidor.server_address[1]}"
    for var in fuente_mcp._URLS:
        monkeypatch.setenv(var, url)
    monkeypatch.setattr(settings, "chat_mcp_dir", str(MCP_DIR))
    yield _Backend
    servidor.shutdown()


def test_lee_el_expediente_por_mcp_con_el_token_del_analista(backend):
    ctx = fuente_mcp.construir(19, TOKEN)

    assert ctx is not None and ctx.case.nombre == "Malspam QakBot"
    assert [f.ref for f in ctx.fuentes] == ["EV1", "EV2", "OS1", "TR1", "TL1", "IN1"]
    # Todas las lecturas, con el JWT de quien pregunta y ninguna otra identidad.
    assert backend.peticiones and {a for _, a in backend.peticiones} == {f"Bearer {TOKEN}"}


def test_solo_se_lee_el_caso_pedido(backend):
    fuente_mcp.construir(19, TOKEN)

    for ruta, _ in backend.peticiones:
        ids = set(re.findall(r"/cases/(\d+)", ruta)) | set(re.findall(r"case_id=(\d+)", ruta))
        assert ids == {"19"}, ruta


def test_la_numeracion_sigue_el_orden_de_la_base_no_el_de_la_api(backend):
    ctx = fuente_mcp.construir(19, TOKEN)

    ev1 = next(f for f in ctx.fuentes if f.ref == "EV1")
    assert ev1.fila_id == "20"  # subida antes, aunque la API la devolviera segunda


def test_el_texto_para_el_modelo_tiene_el_mismo_formato_que_por_sql(backend):
    texto = contexto_mod.a_texto(fuente_mcp.construir(19, TOKEN))

    assert "Caso #19: Malspam QakBot" in texto
    assert "Estado: en_progreso" in texto
    assert "[TR1] evento #7 · 2026-09-26T09:15:40 · severidad=alta · usuario=admin" in texto
    assert "[OS1] indicador #158" in texto and "reputación=low (20)" in texto


def test_caso_inexistente_es_none_no_un_contexto_vacio(backend):
    assert fuente_mcp.construir(999, TOKEN) is None


def test_si_el_backend_falla_el_chat_lo_dice_como_no_disponible(backend, monkeypatch):
    backend.fallar = True
    monkeypatch.setattr(settings, "chat_contexto", "mcp")

    with pytest.raises(service.ChatUnavailableError, match="MCP"):
        service._leer_contexto(db=None, case_id=19, token=TOKEN)


def test_sin_token_no_se_lee_con_otra_identidad(monkeypatch):
    monkeypatch.setattr(settings, "chat_contexto", "mcp")

    with pytest.raises(service.ChatConfigError, match="token"):
        service._leer_contexto(db=None, case_id=19, token="")


def test_el_proceso_mcp_no_hereda_los_secretos_de_informes(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-no-debe-viajar")
    monkeypatch.setenv("DATABASE_URL", "mysql://no-debe-viajar")
    monkeypatch.setenv("CASOS_BASE_URL", "http://casos:8000")

    entorno = fuente_mcp._parametros(TOKEN).env

    assert entorno == {"CASOS_BASE_URL": "http://casos:8000", "MCP_ACCESS_TOKEN": TOKEN}
