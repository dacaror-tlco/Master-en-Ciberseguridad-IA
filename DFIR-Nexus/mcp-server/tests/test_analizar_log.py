"""
Tests de la tool `analizar_log` (Fase 2I, Tracking).

`POST /cases/{case_id}/tracking/analyze` (track-inc/app/modules/tracking/
routes.py) verificado en el código real: sube un fichero de log (multipart,
`UploadFile`) + `zona_horaria` (Form), devuelve una vista previa clasificada
— NO persiste nada (distinto de `/events`, ver Fase 2H). Por eso esta tool
no exige `confirmado`.

Seguridad de rutas (`_validar_ruta_permitida`, app/main.py): sin
`MCP_ALLOWED_FILE_DIRS` configurado, se rechaza CUALQUIER ruta. Con al
menos un directorio permitido, cualquier ruta se resuelve con
`Path.resolve()` (sigue symlinks, neutraliza `..`) y se comprueba que el
resultado queda DENTRO de un directorio permitido — antes de leer nada
del fichero. Estos tests parchean `app.main._DIRECTORIOS_PERMITIDOS`
directamente (no el `.env` real) para tener control total del entorno de
cada caso, con directorios temporales de pytest (`tmp_path`).
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

import app.main as mcp_main
from app.main import analizar_log

TRACKING_BASE_URL = "http://localhost:8001"
CASOS_BASE_URL = "http://localhost:8000"

_RESPUESTA_ANALISIS = {
    "total_eventos": 2,
    "por_severidad": {"media": 2},
    "eventos": [
        {
            "hora": "2026-09-29T10:15:32",
            "evento": "Failed password for invalid user admin from 203.0.113.7 port 51515 ssh2",
            "severidad": "media",
            "usuario_detectado": None,
            "regla": "intento_de_inicio_de_sesion_fallido",
            "reglas": ["intento_de_inicio_de_sesion_fallido"],
            "mitre": ["T1110"],
            "linea_original": "...",
            "numero_linea": 1,
            "hora_inferida": False,
        }
    ],
    "indicadores": [],
    "codificacion": "utf-8",
    "sha256_log": "a" * 64,
    "eventos_ya_guardados": 0,
}


def _mockear_login_ok(token: str = "token-de-prueba") -> respx.Route:
    return respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        return_value=httpx.Response(
            200, json={"access_token": token, "token_type": "bearer", "expires_in": 7200}
        )
    )


@pytest.fixture
def directorio_permitido(tmp_path, monkeypatch):
    """Un único directorio temporal permitido para el test, aislado del
    `.env` real (que apunta a mcp-server/lab_files, usado en la prueba
    real más abajo)."""
    permitido = tmp_path / "permitido"
    permitido.mkdir()
    monkeypatch.setattr(mcp_main, "_DIRECTORIOS_PERMITIDOS", (permitido.resolve(),))
    return permitido


@pytest.fixture
def log_valido(directorio_permitido):
    fichero = directorio_permitido / "auth.log"
    fichero.write_text("Failed password for invalid user admin from 203.0.113.7 port 51515 ssh2\n")
    return fichero


# --- validación de parámetros antes de tocar la red ------------------------


@pytest.mark.asyncio
async def test_case_id_no_positivo_se_rechaza_antes_que_la_ruta(directorio_permitido):
    with pytest.raises(ToolError, match="entero positivo"):
        await analizar_log(0, str(directorio_permitido / "no-existe.log"))


@pytest.mark.asyncio
async def test_zona_horaria_invalida_se_rechaza_antes_que_la_ruta(log_valido):
    with pytest.raises(ToolError, match="zona_horaria"):
        await analizar_log(8, str(log_valido), zona_horaria="Europe/Madrid")


# --- sin ningún directorio permitido configurado ----------------------------


@pytest.mark.asyncio
async def test_sin_directorios_permitidos_configurados_se_rechaza_cualquier_ruta(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_main, "_DIRECTORIOS_PERMITIDOS", ())
    with pytest.raises(ToolError, match="MCP_ALLOWED_FILE_DIRS"):
        await analizar_log(8, str(tmp_path / "cualquiera.log"))


# --- controles de fichero ----------------------------------------------


@pytest.mark.asyncio
async def test_fichero_inexistente_se_rechaza(directorio_permitido):
    with pytest.raises(ToolError, match="no existe"):
        await analizar_log(8, str(directorio_permitido / "no-existe.log"))


@pytest.mark.asyncio
async def test_directorio_en_vez_de_fichero_se_rechaza(directorio_permitido):
    subdir = directorio_permitido / "subcarpeta"
    subdir.mkdir()
    with pytest.raises(ToolError, match="es un directorio"):
        await analizar_log(8, str(subdir))


@pytest.mark.asyncio
async def test_ruta_con_byte_nulo_se_rechaza_como_toolerror(directorio_permitido):
    """Encontrado en la auditoría final (Fase 2A-2I): un byte nulo embebido
    en la ruta hacía que Path.resolve() lanzara ValueError, no capturado
    antes por `_validar_ruta_permitida` — la tool completa fallaba con una
    excepción cruda en vez de un ToolError claro. Corregido añadiendo
    ValueError al except ya existente (junto a OSError/RuntimeError)."""
    with pytest.raises(ToolError, match="ruta inválida"):
        await analizar_log(8, str(directorio_permitido) + "/algo\x00malo.log")


@pytest.mark.asyncio
async def test_path_traversal_fuera_del_permitido_se_rechaza(directorio_permitido, tmp_path):
    fuera = tmp_path / "fuera"
    fuera.mkdir()
    (fuera / "secreto.log").write_text("contenido")
    ruta_con_traversal = str(directorio_permitido / ".." / "fuera" / "secreto.log")

    with pytest.raises(ToolError, match="fuera de los directorios permitidos"):
        await analizar_log(8, ruta_con_traversal)


@pytest.mark.asyncio
async def test_ruta_fuera_de_la_allowlist_se_rechaza(directorio_permitido, tmp_path):
    otro_dir = tmp_path / "otro-directorio-no-permitido"
    otro_dir.mkdir()
    otro_fichero = otro_dir / "auth.log"
    otro_fichero.write_text("contenido")

    with pytest.raises(ToolError, match="fuera de los directorios permitidos"):
        await analizar_log(8, str(otro_fichero))


@pytest.mark.asyncio
async def test_symlink_que_escapa_del_permitido_se_rechaza(directorio_permitido, tmp_path):
    fuera = tmp_path / "fuera-del-symlink"
    fuera.mkdir()
    objetivo = fuera / "real.log"
    objetivo.write_text("contenido real fuera del directorio permitido")

    enlace = directorio_permitido / "enlace.log"
    try:
        enlace.symlink_to(objetivo)
    except (OSError, NotImplementedError):
        pytest.skip("El sistema de ficheros no permite crear symlinks en este entorno.")

    with pytest.raises(ToolError, match="fuera de los directorios permitidos"):
        await analizar_log(8, str(enlace))


@pytest.mark.asyncio
async def test_fichero_demasiado_grande_se_rechaza_sin_leerlo(directorio_permitido, monkeypatch):
    monkeypatch.setattr(mcp_main, "_MAX_LOG_BYTES_CLIENTE", 10)
    fichero = directorio_permitido / "grande.log"
    fichero.write_bytes(b"x" * 11)

    with pytest.raises(ToolError, match="por encima del límite"):
        await analizar_log(8, str(fichero))


# --- confirmado=True: éxito ------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_fichero_valido_analiza_y_devuelve_los_datos_reales(log_valido):
    _mockear_login_ok()
    ruta_http = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(200, json=_RESPUESTA_ANALISIS)
    )

    resultado = await analizar_log(8, str(log_valido))

    assert resultado == {"estado": "ok", "datos": _RESPUESTA_ANALISIS}
    peticion_enviada = ruta_http.calls.last.request
    assert peticion_enviada.headers["content-type"].startswith("multipart/form-data")
    assert b"Failed password for invalid user admin" in peticion_enviada.content
    assert b"zona_horaria" in peticion_enviada.content
    # Nunca base64: el fichero viaja tal cual dentro del multipart, no
    # codificado como texto en un campo JSON.
    import base64

    assert base64.b64encode(log_valido.read_bytes()) not in peticion_enviada.content


@pytest.mark.asyncio
@respx.mock
async def test_zona_horaria_con_desplazamiento_se_envia_tal_cual(log_valido):
    _mockear_login_ok()
    ruta_http = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(200, json=_RESPUESTA_ANALISIS)
    )

    resultado = await analizar_log(8, str(log_valido), zona_horaria="+02:00")

    assert resultado["estado"] == "ok"
    assert b"+02:00" in ruta_http.calls.last.request.content


# --- no encontrado / conflicto ----------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_caso_inexistente_es_no_encontrado(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/999/tracking/analyze").mock(
        return_value=httpx.Response(404, json={"detail": "No existe ningún caso con id=999"})
    )

    resultado = await analizar_log(999, str(log_valido))

    assert resultado == {"estado": "no_encontrado", "detalle": "No existe ningún caso con id=999"}


@pytest.mark.asyncio
@respx.mock
async def test_caso_no_modificable_es_conflicto(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(409, json={"detail": "El caso está eliminado"})
    )

    resultado = await analizar_log(8, str(log_valido))

    assert resultado == {"estado": "conflicto", "detalle": "El caso está eliminado"}


# --- formato inválido (400 real del backend) --------------------------


@pytest.mark.asyncio
@respx.mock
async def test_fichero_no_es_texto_se_propaga_como_error_claro_sin_contenido(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(400, json={"detail": "No es un fichero de texto legible."})
    )

    with pytest.raises(ToolError, match="No es un fichero de texto legible"):
        await analizar_log(8, str(log_valido))


@pytest.mark.asyncio
@respx.mock
async def test_413_fichero_demasiado_grande_segun_el_backend_real(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(413, json={"detail": "El fichero supera el máximo de 20 MB."})
    )

    with pytest.raises(ToolError, match="rechazado el fichero por tamaño"):
        await analizar_log(8, str(log_valido))


# --- 401 + reautenticación ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_401_reautentica_una_vez_y_repite_la_peticion(log_valido):
    login = respx.post(f"{CASOS_BASE_URL}/auth/login").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "token-viejo", "token_type": "bearer", "expires_in": 7200}),
            httpx.Response(200, json={"access_token": "token-nuevo", "token_type": "bearer", "expires_in": 7200}),
        ]
    )
    peticion = respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "No autenticado"}),
            httpx.Response(200, json=_RESPUESTA_ANALISIS),
        ]
    )

    resultado = await analizar_log(8, str(log_valido))

    assert resultado["estado"] == "ok"
    assert login.call_count == 2
    assert peticion.call_count == 2
    assert peticion.calls.last.request.headers["authorization"] == "Bearer token-nuevo"


# --- segundo 401 -------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_segundo_401_no_reintenta_mas_y_falla_con_claridad(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(401, json={"detail": "No autenticado"})
    )

    with pytest.raises(ToolError, match="dos veces seguidas"):
        await analizar_log(8, str(log_valido))


# --- 422 -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_422_se_propaga_como_error_claro(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(
        return_value=httpx.Response(422, json={"detail": "petición inválida"})
    )

    with pytest.raises(ToolError, match="422"):
        await analizar_log(8, str(log_valido))


# --- 5xx -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_5xx_se_propaga_como_error_claro(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(return_value=httpx.Response(500))

    with pytest.raises(ToolError, match="error del servidor"):
        await analizar_log(8, str(log_valido))


# --- timeout/error de conexión ---------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_error_de_conexion_se_propaga_como_error_claro(log_valido):
    respx.post(f"{CASOS_BASE_URL}/auth/login").mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(ToolError, match="No se ha podido autenticar"):
        await analizar_log(8, str(log_valido))


@pytest.mark.asyncio
@respx.mock
async def test_timeout_se_propaga_como_error_claro(log_valido):
    _mockear_login_ok()
    respx.post(f"{TRACKING_BASE_URL}/cases/8/tracking/analyze").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(ToolError, match="No se ha podido conectar"):
        await analizar_log(8, str(log_valido))


# -----------------------------------------------------------------------------
# Prueba real contra Tracking local (SIN mocks). Usa el fichero de
# laboratorio controlado y sintético `mcp-server/lab_files/auth_lab.log`
# (4 líneas, sin datos personales ni reales: IPs/usuarios de ejemplo,
# ver RFC 5737/RFC 2606) — el `.env` real ya apunta MCP_ALLOWED_FILE_DIRS a
# ese directorio. Crea su propio caso de prueba (vía crear_caso, Fase 2G)
# y comprueba que el resultado llega de verdad desde MCP -> REST -> backend
# (al menos un evento clasificado, con severidad reconocida).
# -----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_real_contra_tracking_local_si_esta_disponible():
    email = os.environ.get("MCP_SERVICE_EMAIL")
    password = os.environ.get("MCP_SERVICE_PASSWORD")
    if not email or not password:
        pytest.skip("MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD no están en el entorno de test.")

    import app.core.config as config_module

    config_module.settings.MCP_SERVICE_EMAIL = email
    config_module.settings.MCP_SERVICE_PASSWORD = password

    if not mcp_main._DIRECTORIOS_PERMITIDOS:
        pytest.skip(
            "MCP_ALLOWED_FILE_DIRS no está configurado en mcp-server/.env: sin él, "
            "analizar_log rechaza cualquier ruta por diseño."
        )

    from datetime import datetime, timezone

    from app.main import crear_caso

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nombre_caso = f"MCP-TEST-Fase2I-analizar_log-{marca}"

    try:
        caso = await crear_caso(nombre_caso, "MCP Server (test automático)", confirmado=True)
    except ToolError as exc:
        pytest.skip(f"Casos no disponible en {CASOS_BASE_URL}, o credenciales rechazadas: {exc}")

    assert caso["estado"] == "ok"
    case_id = caso["datos"]["id"]

    ruta_lab = str((mcp_main._DIRECTORIOS_PERMITIDOS[0] / "auth_lab.log"))
    if not os.path.exists(ruta_lab):
        pytest.skip(f"No existe el fichero de laboratorio esperado: {ruta_lab}")

    try:
        resultado = await analizar_log(case_id, ruta_lab)
    except ToolError as exc:
        pytest.skip(f"Tracking no disponible en {TRACKING_BASE_URL}, o credenciales rechazadas: {exc}")

    assert resultado["estado"] == "ok"
    datos = resultado["datos"]
    assert datos["total_eventos"] >= 1
    assert datos["eventos"]

    print(
        f"\n[test_real_contra_tracking_local_si_esta_disponible] Caso de prueba id={case_id} "
        f"nombre={nombre_caso!r}, fichero de laboratorio '{ruta_lab}' analizado: "
        f"{datos['total_eventos']} eventos detectados (nada persistido)."
    )
