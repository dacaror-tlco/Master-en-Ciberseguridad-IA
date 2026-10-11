"""
Punto de entrada del MCP Server de Nexus.

Fase 2A + 2B + 2C + 2D + 2E: trece tools de solo lectura —
`consultar_caso`, `buscar_casos`, `consultar_auditoria_caso` (Fase 2A,
Casos); `listar_evidencias_de_caso`, `consultar_evidencia`,
`verificar_integridad_evidencia` (Fase 2B, sub-recurso de Casos: las
evidencias no tienen backend propio, ver CLAUDE.md);
`obtener_cronologia_caso` (Fase 2C, Timeline, puerto 8002),
`listar_informes_de_caso` y `consultar_informe` (Fase 2C, Informes,
puerto 8003); `listar_eventos_tracking` y `verificar_integridad_tracking`
(Fase 2D, Tracking, puerto 8001 — sin `consultar_evento_tracking`:
Tracking no expone ningún endpoint REST de consulta individual de
evento, ver README); `listar_hallazgos_osint` y `consultar_hallazgo_osint`
(Fase 2E, OSINT, puerto 8124 — sobre `/osint-findings`, la vista de
lectura consolidada de los 8 tipos de análisis OSINT; ningún análisis
nuevo, ver README).

Fase 2F: `recalcular_cronologia` — la primera tool de escritura. Requiere
`confirmado=true` explícito (ver su docstring y el README para el
mecanismo de protección).

Fase 2G: `crear_caso`, `cambiar_estado_caso` (Casos) y `vincular_hallazgo`
(OSINT, `/osint-cases/{case_type}/{id}/vinculacion` — resuelve
case_type/source_id a partir del finding_id vía `/osint-findings/{id}`,
nunca desvincula). Las tres exigen `confirmado=true` explícito con el
mismo mecanismo que `recalcular_cronologia`: comprobado antes de
cualquier petición HTTP, ni siquiera de lectura.

Fase 2H: `registrar_evidencia` (Casos — nunca calcula ni envía el hash de
integridad, lo calcula el backend), `guardar_eventos_tracking` (Tracking
— persiste eventos ya clasificados, no analiza ningún log) y
`generar_informe` (Informes — COSTE ECONÓMICO REAL, llamada a IA). Mismo
mecanismo de `confirmado` obligatorio que las fases anteriores.

Habla exclusivamente por HTTP con los backends — nunca importa su
código, igual que ya hace el frontend (ver CLAUDE.md: "un módulo nunca
debe importar otro módulo", regla que también aplica a este proceso
nuevo frente a los 5 backends existentes). Un solo login (contra Casos,
único backend que emite JWT) autentica las peticiones a los cinco
backends, porque comparten `JWT_SECRET` (ver app/core/auth.py).
Transporte stdio: no levanta ningún servidor de red propio, Claude Code
lo lanza como subproceso.

Fase 2I: `analizar_log` (Tracking — sube un fichero LOCAL dentro de
`MCP_ALLOWED_FILE_DIRS`, vía multipart, nunca base64; no persiste, sin
`confirmado`) y `analizar_dominio` (OSINT — la única de las 8 tools de
análisis OSINT expuesta esta fase, la de menor riesgo: sin fichero, sin
PII; SÍ persiste un hallazgo nuevo, así que SÍ exige `confirmado=true`).

`descargar_informe`, el resto de análisis OSINT que ejecutan trabajo
real (`analizar_email`, `analizar_wallet`, `analizar_typosquatting`,
`analizar_telefono`, `verificar_cnmv`, `analizar_imagen`, `analizar_ip`),
`DELETE /cases/{id}`, desvincular un hallazgo, editar/borrar evidencias,
y cualquier otra tool de escritura quedan fuera de esta fase a propósito
(ver la auditoría de diseño de la Fase MCP 2).
"""

from __future__ import annotations

import re
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from app.core.auth import CasosAuthError
from app.core.config import settings
from app.core.http_client import (
    casos_session,
    informes_client,
    osint_client,
    timeline_client,
    tracking_client,
)

mcp = FastMCP(name="dfir-nexus")

# Solo lectura: sin `confirmado`, con las pistas de protocolo que
# corresponden (ver diseño de la Fase MCP 2, §4 y §6). `ToolAnnotations`
# es informativo para el cliente, no una barrera de seguridad — la
# barrera real, cuando haga falta, será el parámetro `confirmado` en las
# tools de escritura.
_SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, destructiveHint=False)

# Escritura destructiva (Fase 2F): la pista de protocolo por sí sola NO
# es la protección real — ver el docstring de `recalcular_cronologia` y
# el README para el mecanismo que sí lo es (`confirmado: bool`
# obligatorio, comprobado en código antes de tocar la red).
_ESCRITURA_DESTRUCTIVA = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False)

_ESTADOS_VALIDOS = {"abierto", "en_progreso", "cerrado", "archivado"}
"""Duplicado deliberadamente de `backend/app/modules/cases/models.py::EstadoCaso`
(mismo criterio que los 5 backends duplican, en vez de importar, la
verificación de JWT entre sí): este proceso no importa código de Casos."""

_SEVERIDADES_TRACKING_VALIDAS = {"baja", "media", "alta", "critica"}
"""Duplicado deliberadamente de `track-inc/app/modules/tracking/models.py::Severidad`
— mismo criterio que `_ESTADOS_VALIDOS`."""

_MAX_EVENTOS_TRACKING_POR_LLAMADA = 500
"""Límite propio de ESTA tool (`guardar_eventos_tracking`), no del backend de
Tracking: su esquema (`SaveEventsRequest.eventos`) no impone ningún máximo.
Guarda frente a una petición desproporcionada por error (p. ej. pegar un log
entero sin pasar por /analyze) — no es un límite de negocio documentado en
CLAUDE.md, es una cautela de esta tool."""

# Análisis (Fase 2I): ni solo-lectura ni "escritura destructiva" en el
# sentido de las demás — `readOnlyHint=False` porque ejecuta trabajo real
# (clasificación de un fichero completo), pero no persiste nada, así que
# no lleva `confirmado` (ver enunciado: "No añadir confirmado salvo que
# la operación produzca una mutación persistente"). Usada solo por
# `analizar_log`.
_ANALISIS_SIN_PERSISTENCIA = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True)

_DIRECTORIOS_PERMITIDOS: tuple[Path, ...] = tuple(
    Path(d.strip()).resolve()
    for d in settings.MCP_ALLOWED_FILE_DIRS.split(",")
    if d.strip()
)
"""Calculado UNA vez al importar el módulo, a partir de MCP_ALLOWED_FILE_DIRS
(mcp-server/.env) — vacío por defecto, a propósito (ver config.py):
`analizar_log` rechaza cualquier ruta hasta que se configure al menos un
directorio explícitamente."""

_MAX_LOG_BYTES_CLIENTE = 20 * 1024 * 1024
"""Límite propio de ESTA tool (`analizar_log`), como aviso rápido ANTES de
leer el fichero entero en memoria — coincide con el valor por defecto real
de Tracking (`TRACKING_MAX_LOG_MB`, track-inc/app/modules/tracking/
routes.py::_max_bytes_log), pero no es autoritativo: si ese backend cambia
su propio límite, el 413 real que devuelva sigue siendo la última palabra,
esta tool solo evita una subida innecesaria cuando ya se sabe que fallará."""

_ZONA_HORARIA_RE = re.compile(r"^(UTC|Z|[+-]\d{2}:\d{2})$", re.IGNORECASE)
"""Validación ligera, ANTES de tocar la red: acepta lo mismo que documenta
`_analizar`/`parsear_zona` en Tracking (UTC o un desplazamiento tipo
'+02:00'). No reimplementa los rangos exactos que valida el backend
(p. ej. horas 00-14): un valor con la forma correcta pero fuera de rango
se deja para el 400 real del backend, no se intenta adivinar aquí."""


def _validar_ruta_permitida(ruta_str: str) -> Path:
    """Resuelve `ruta_str` y comprueba que el resultado queda DENTRO de un
    directorio de `_DIRECTORIOS_PERMITIDOS` — nunca acepta nada fuera de esa
    lista, ni por path traversal (`../..`) ni por symlink: `Path.resolve()`
    seguido de la comprobación de contención cubre ambos casos a la vez,
    porque el resultado de `resolve()` YA es la ruta real final, sea cual sea
    el camino (relativo, con `..`, o a través de un enlace) que se usó para
    llegar a ella.

    No revela el contenido del fichero en ningún mensaje de error — como
    mucho, la propia ruta que ya dio quien llama."""
    if not ruta_str or not ruta_str.strip():
        raise ToolError("ruta no puede estar vacía.")
    if not _DIRECTORIOS_PERMITIDOS:
        raise ToolError(
            "No hay ningún directorio permitido configurado (MCP_ALLOWED_FILE_DIRS en "
            "mcp-server/.env): por seguridad, esta tool rechaza cualquier ruta hasta que se "
            "configure explícitamente al menos uno."
        )

    try:
        resuelta = Path(ruta_str).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        # ValueError: p. ej. un byte nulo embebido en la ruta (encontrado en
        # la auditoría final, Fase 2A-2I) — antes escapaba sin envolver en
        # ToolError, igual que el RuntimeError de un bucle de symlinks
        # (ya cubierto) o un OSError de resolución.
        raise ToolError(f"ruta inválida: {exc}") from exc

    permitida = any(resuelta == d or resuelta.is_relative_to(d) for d in _DIRECTORIOS_PERMITIDOS)
    if not permitida:
        raise ToolError(
            f"La ruta '{ruta_str}' (resuelta a '{resuelta}') queda fuera de los directorios "
            "permitidos (MCP_ALLOWED_FILE_DIRS). Rechazada por seguridad, incluida cualquier "
            "ruta que llegue ahí mediante '..' o un enlace simbólico."
        )
    if not resuelta.exists():
        raise ToolError(f"La ruta '{ruta_str}' no existe.")
    if resuelta.is_dir():
        raise ToolError(f"La ruta '{ruta_str}' es un directorio, no un fichero.")
    if not resuelta.is_file():
        raise ToolError(f"La ruta '{ruta_str}' no es un fichero regular.")

    tamano = resuelta.stat().st_size
    if tamano > _MAX_LOG_BYTES_CLIENTE:
        raise ToolError(
            f"El fichero '{ruta_str}' pesa {tamano} bytes, por encima del límite de esta tool "
            f"({_MAX_LOG_BYTES_CLIENTE} bytes ≈ {_MAX_LOG_BYTES_CLIENTE // (1024 * 1024)} MB, "
            "el mismo valor por defecto que Tracking documenta para este mismo límite real)."
        )

    return resuelta


async def _peticion_segura(
    method: str,
    path: str,
    *,
    client: httpx.AsyncClient | None = None,
    backend: str = "Casos",
    **kwargs: object,
) -> httpx.Response:
    """Envuelve `casos_session.request` traduciendo los fallos de
    autenticación/conexión a `ToolError`, y propaga como `ToolError` los
    códigos de error que todas las tools de este módulo tratan igual (401
    tras reautenticar, 422, 5xx). 200 y 404 los interpreta cada tool,
    porque su significado depende de qué se pidió.

    `client` dirige la petición a Timeline/Informes en vez de Casos (por
    defecto); `backend` es solo para que el mensaje de error nombre el
    backend correcto — el login sigue siendo siempre contra Casos (ver
    auth.py), sea cual sea el destino de la petición.

    Punto único para no repetir este bloque en cada tool nueva — ver
    diseño Fase MCP 2, "evita duplicar lógica".
    """
    try:
        response = await casos_session.request(method, path, client=client, **kwargs)
    except CasosAuthError as exc:
        raise ToolError(f"No se ha podido autenticar contra Casos: {exc}") from exc
    except httpx.RequestError as exc:
        raise ToolError(f"No se ha podido conectar con {backend}: {exc}") from exc

    if response.status_code == 401:
        raise ToolError(
            f"{backend} ha rechazado la autenticación dos veces seguidas (401): "
            "revisa las credenciales del usuario de servicio en mcp-server/.env."
        )
    if response.status_code == 422:
        raise ToolError(f"{backend} ha rechazado la petición como inválida (422): {response.text}")
    if response.status_code >= 500:
        # Incluye el `detail` real si el backend lo trae (p. ej. Informes
        # devuelve 502/503 con un motivo real de IA — no disponible,
        # respuesta no firmable — no un 500 genérico; ver generar_informe,
        # Fase 2H): más útil que un mensaje ciego, y no cambia el criterio
        # de error para ningún tool ya existente (sigue siendo ToolError).
        raise ToolError(
            f"{backend} ha respondido con un error del servidor "
            f"({response.status_code}): {_detalle_backend(response, response.text)}"
        )

    return response


def _detalle_backend(response: httpx.Response, respaldo: str) -> str:
    """Extrae el campo `detail` real que devuelve Casos en un error, para
    distinguir p. ej. "Caso no encontrado" de "Evidencia no encontrada"
    (mismo código HTTP 404, mensajes distintos — ver
    backend/app/modules/cases/routes.py). Si el cuerpo no es JSON o no
    trae `detail`, usa `respaldo` en vez de fallar."""
    try:
        cuerpo = response.json()
    except ValueError:
        return respaldo
    detalle = cuerpo.get("detail") if isinstance(cuerpo, dict) else None
    return detalle if isinstance(detalle, str) else respaldo


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Consulta el detalle de un caso de Nexus por su identificador numérico "
        "(case_id). Úsala cuando el usuario pida ver, comprobar o consultar un "
        "caso concreto del que ya conoce el número. Devuelve nombre, estado, "
        "responsable, descripción y fechas del caso. Si no existe ningún caso "
        "con ese id, lo indica explícitamente (encontrado=false) en vez de "
        "inventar datos."
    )
)
async def consultar_caso(case_id: int) -> dict:
    # Validación semántica antes de llamar a Casos: `int` ya lo garantiza el
    # esquema de la tool, pero 0 o negativo es sintácticamente un entero
    # válido y semánticamente no puede ser un id real.
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura("GET", f"/cases/{case_id}")

    if response.status_code == 404:
        # No es un fallo de la tool: es una respuesta válida ("ese caso no
        # existe"). Se devuelve como resultado normal, no como ToolError,
        # para que Claude lo comunique sin tratarlo como un error de sistema.
        return {
            "encontrado": False,
            "case_id": case_id,
            "mensaje": f"No existe ningún caso con id={case_id} en Nexus.",
        }

    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"encontrado": True, "caso": response.json()}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Busca casos de Nexus, opcionalmente filtrando por estado y/o por "
        "texto libre. Úsala cuando el usuario pida listar, buscar o ver "
        "qué casos hay (p. ej. 'los casos abiertos', 'busca el caso del "
        "ransomware'), a diferencia de consultar_caso, que es para un id "
        "concreto ya conocido. Sin filtros, devuelve todos los casos. "
        "estado debe ser exactamente uno de: abierto, en_progreso, "
        "cerrado, archivado. texto busca coincidencia parcial (sin "
        "distinguir mayúsculas/minúsculas) en el nombre, el responsable y "
        "la descripción del caso. Si se indican los dos filtros a la vez, "
        "se aplican ambos (un caso debe cumplir los dos)."
    )
)
async def buscar_casos(estado: str | None = None, texto: str | None = None) -> dict:
    if estado is not None and estado not in _ESTADOS_VALIDOS:
        raise ToolError(
            f"estado={estado!r} no es válido. Debe ser uno de: {', '.join(sorted(_ESTADOS_VALIDOS))}."
        )
    # Cadena vacía o solo espacios: se trata como "sin filtro de texto", no
    # como un filtro que no puede casar con nada.
    texto_normalizado = texto.strip().lower() if texto and texto.strip() else None

    response = await _peticion_segura("GET", "/cases")
    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    casos = response.json()

    if estado is not None:
        casos = [c for c in casos if c.get("estado") == estado]

    if texto_normalizado is not None:
        def _coincide(caso: dict) -> bool:
            campos = (caso.get("nombre"), caso.get("responsable"), caso.get("descripcion"))
            return any(campo and texto_normalizado in campo.lower() for campo in campos)

        casos = [c for c in casos if _coincide(c)]

    return {"estado": "ok", "datos": {"total": len(casos), "casos": casos}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Consulta el historial de auditoría de un caso de Nexus (altas, "
        "ediciones, cambios de estado, borrados, y lo mismo para sus "
        "evidencias). Úsala cuando el usuario pregunte qué ha pasado con "
        "un caso, quién lo modificó o cuándo. Requiere el case_id exacto. "
        "Si el caso no existe, lo indica explícitamente en vez de "
        "inventar un historial."
    )
)
async def consultar_auditoria_caso(case_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura("GET", f"/cases/{case_id}/auditoria")

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": f"No existe ningún caso con id={case_id} en Nexus.",
        }

    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": {"entradas": response.json()}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Lista las evidencias registradas en un caso de Nexus (tipo, valor, "
        "huella SHA-256, observaciones, fechas). Las evidencias son un "
        "sub-recurso de Casos: no hay ningún backend ni id independiente "
        "para ellas fuera de un caso concreto. Úsala cuando el usuario "
        "pregunte qué evidencias tiene un caso. Si el caso no existe, lo "
        "indica explícitamente; si existe pero no tiene evidencias, lo "
        "indica igualmente (sin_resultados), que es distinto de que el "
        "caso no exista."
    )
)
async def listar_evidencias_de_caso(case_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura("GET", f"/cases/{case_id}/evidences")

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id} en Nexus."),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    evidencias = response.json()
    if not evidencias:
        # Distinto de "no_encontrado": el caso SÍ existe, solo que no tiene
        # evidencias todavía (o todas están borradas lógicamente — el
        # backend excluye las eliminadas por defecto, mismo criterio que
        # usa el frontend).
        return {
            "estado": "sin_resultados",
            "detalle": f"El caso {case_id} no tiene evidencias registradas.",
        }

    return {"estado": "ok", "datos": {"total": len(evidencias), "evidencias": evidencias}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Consulta el detalle de una evidencia concreta de un caso de Nexus "
        "(tipo, valor, huella SHA-256 registrada, observaciones, fecha de "
        "adquisición y de subida). Requiere tanto case_id como "
        "evidence_id: una evidencia no se identifica por sí sola, siempre "
        "pertenece a un caso. Si el caso o la evidencia no existen, lo "
        "indica explícitamente (y distingue cuál de los dos falta) en vez "
        "de inventar datos."
    )
)
async def consultar_evidencia(case_id: int, evidence_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if evidence_id <= 0:
        raise ToolError("evidence_id debe ser un entero positivo.")

    response = await _peticion_segura("GET", f"/cases/{case_id}/evidences/{evidence_id}")

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(
                response, f"No se encontró la evidencia {evidence_id} del caso {case_id}."
            ),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Verifica la integridad de una evidencia: recalcula el SHA-256 de "
        "su contenido (`valor`) y lo compara con la huella que se guardó "
        "al crearla. Devuelve el algoritmo, el hash registrado, el hash "
        "actual y si coinciden (integro=true/false). integro=false "
        "significa que el contenido cambió por una vía que no fue la API "
        "normal, que nunca permite editar tipo/valor tras crear la "
        "evidencia. Esta tool solo lee y compara — no modifica nada. Si el "
        "caso o la evidencia no existen, lo indica explícitamente."
    )
)
async def verificar_integridad_evidencia(case_id: int, evidence_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if evidence_id <= 0:
        raise ToolError("evidence_id debe ser un entero positivo.")

    response = await _peticion_segura("GET", f"/cases/{case_id}/evidences/{evidence_id}/integridad")

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(
                response, f"No se encontró la evidencia {evidence_id} del caso {case_id}."
            ),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Obtiene la cronología consolidada (timeline) de un caso de Nexus: "
        "los eventos de evidencias, hallazgos OSINT y tracking ya "
        "correlacionados en orden temporal. Úsala cuando el usuario pida "
        "ver la línea temporal o el orden de los hechos de un caso. "
        "Limitación conocida: el backend de Timeline no comprueba si el "
        "case_id corresponde a un caso real — un case_id inexistente "
        "devuelve el mismo resultado vacío (sin_resultados) que un caso "
        "real sin eventos todavía; esta tool no puede distinguir los dos "
        "casos porque el backend tampoco lo hace."
    )
)
async def obtener_cronologia_caso(case_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura(
        "GET", f"/timeline/cases/{case_id}", client=timeline_client, backend="Timeline"
    )

    if response.status_code != 200:
        raise ToolError(
            f"Timeline ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    eventos = response.json()
    if not eventos:
        # Ver la limitación documentada en la descripción de la tool: no se
        # puede saber aquí si es porque el caso no existe o porque existe
        # pero no tiene cronología calculada todavía.
        return {
            "estado": "sin_resultados",
            "detalle": f"El caso {case_id} no tiene eventos en la cronología (o no existe).",
        }

    return {"estado": "ok", "datos": {"total": len(eventos), "eventos": eventos}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Lista los informes periciales emitidos para un caso de Nexus "
        "(versión, fecha, quién lo generó, notas, huellas SHA-256). No "
        "genera ningún informe nuevo, solo consulta los ya existentes. "
        "Úsala cuando el usuario pregunte qué informes tiene un caso. "
        "Limitación conocida: el backend de Informes no comprueba si el "
        "case_id corresponde a un caso real — un case_id inexistente "
        "devuelve el mismo resultado vacío (sin_resultados) que un caso "
        "real sin informes todavía."
    )
)
async def listar_informes_de_caso(case_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura(
        "GET", f"/cases/{case_id}/reports", client=informes_client, backend="Informes"
    )

    if response.status_code != 200:
        raise ToolError(
            f"Informes ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    informes = response.json()
    if not informes:
        return {
            "estado": "sin_resultados",
            "detalle": f"El caso {case_id} no tiene informes emitidos (o no existe).",
        }

    return {"estado": "ok", "datos": {"total": len(informes), "informes": informes}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Consulta los metadatos de un informe pericial concreto de Nexus "
        "por su report_id: versión, fecha de emisión, quién lo generó, "
        "notas, huellas SHA-256 y el resumen redactado por IA. No genera "
        "el informe ni descarga ningún fichero — el campo archivo_pdf que "
        "devuelve es solo una ruta interna del servidor de Informes, "
        "tratarla como metadata, no como algo que esta tool pueda leer o "
        "copiar (la descarga es una capacidad futura aparte). Si no "
        "existe ningún informe con ese id, lo indica explícitamente."
    )
)
async def consultar_informe(report_id: int) -> dict:
    if report_id <= 0:
        raise ToolError("report_id debe ser un entero positivo.")

    response = await _peticion_segura(
        "GET", f"/reports/{report_id}", client=informes_client, backend="Informes"
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún informe con id={report_id}."),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Informes ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Lista los eventos de tracking (post-incidente) ya guardados en un "
        "caso de Nexus: hora, comando/evento, severidad, fuente del log y "
        "usuario detectado. No analiza ni guarda ningún log nuevo, solo "
        "consulta lo que ya se persistió. Admite paginación real del "
        "backend: skip (por defecto 0) y limit (por defecto 100, máximo "
        "1000). Si el caso no existe, lo indica explícitamente; si existe "
        "pero no tiene eventos, también (sin_resultados), que es distinto "
        "de que el caso no exista."
    )
)
async def listar_eventos_tracking(case_id: int, skip: int = 0, limit: int = 100) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if skip < 0:
        raise ToolError("skip no puede ser negativo.")
    if not (1 <= limit <= 1000):
        raise ToolError("limit debe estar entre 1 y 1000 (mismo límite que impone el backend de Tracking).")

    response = await _peticion_segura(
        "GET",
        f"/cases/{case_id}/tracking/events",
        client=tracking_client,
        backend="Tracking",
        params={"skip": skip, "limit": limit},
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id} en Nexus."),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Tracking ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    eventos = response.json()
    if not eventos:
        return {
            "estado": "sin_resultados",
            "detalle": f"El caso {case_id} no tiene eventos de tracking guardados.",
        }

    return {"estado": "ok", "datos": {"total": len(eventos), "eventos": eventos, "skip": skip, "limit": limit}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Verifica la integridad de la cadena de eventos de tracking de un "
        "caso de Nexus: compara internamente lo guardado en tracking_events "
        "contra la cadena de hashes local del backend, y devuelve un "
        "veredicto (ok/mensaje) más la lista de eventos que no cuadran, si "
        "los hay — modificados, borrados o insertados por fuera de la "
        "aplicación. Deliberadamente no incluye hashes ni detalle "
        "criptográfico (el propio backend los omite en su respuesta): esta "
        "tool solo reenvía el veredicto, no recalcula ni verifica nada por "
        "su cuenta. Si el caso no existe, lo indica explícitamente."
    )
)
async def verificar_integridad_tracking(case_id: int) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    response = await _peticion_segura(
        "GET", f"/cases/{case_id}/tracking/verify", client=tracking_client, backend="Tracking"
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id} en Nexus."),
        }

    if response.status_code != 200:
        raise ToolError(
            f"Tracking ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Lista hallazgos OSINT (dominio, email, wallet, typosquatting, "
        "teléfono, CNMV, IP, imagen) desde la vista consolidada de Nexus. "
        "No ejecuta ningún análisis nuevo, solo consulta los ya hechos. "
        "Todos los filtros son opcionales y se combinan con AND: case_type "
        "(tipo de análisis), subject_type, subject_value (coincidencia "
        "exacta), case_id (expediente de Nexus al que está vinculado el "
        "hallazgo), risk_level ('low'/'medium'/'high'), min_risk_score "
        "(0-100), since (fecha ISO 8601: solo análisis posteriores). "
        "Admite paginación real del backend: skip (por defecto 0) y limit "
        "(por defecto 50, máximo 200)."
    )
)
async def listar_hallazgos_osint(
    case_type: str | None = None,
    subject_type: str | None = None,
    subject_value: str | None = None,
    case_id: int | None = None,
    risk_level: str | None = None,
    min_risk_score: int | None = None,
    since: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    if skip < 0:
        raise ToolError("skip no puede ser negativo.")
    if not (1 <= limit <= 200):
        raise ToolError("limit debe estar entre 1 y 200 (mismo límite que impone el backend de OSINT).")
    if min_risk_score is not None and not (0 <= min_risk_score <= 100):
        raise ToolError("min_risk_score debe estar entre 0 y 100.")
    if case_id is not None and case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    parametros_completos = {
        "case_type": case_type,
        "subject_type": subject_type,
        "subject_value": subject_value,
        "case_id": case_id,
        "risk_level": risk_level,
        "min_risk_score": min_risk_score,
        "since": since,
        "skip": skip,
        "limit": limit,
    }
    # Los filtros no indicados no se envían: un `None` literal en la query
    # (?case_type=None) no es lo mismo que omitir el parámetro, y el
    # backend distingue "sin filtro" de "filtra por la cadena None".
    params = {clave: valor for clave, valor in parametros_completos.items() if valor is not None}

    response = await _peticion_segura(
        "GET", "/osint-findings", client=osint_client, backend="OSINT", params=params
    )

    if response.status_code != 200:
        raise ToolError(
            f"OSINT ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    hallazgos = response.json()
    if not hallazgos:
        return {
            "estado": "sin_resultados",
            "detalle": "Ningún hallazgo OSINT coincide con los filtros indicados.",
        }

    return {"estado": "ok", "datos": {"total": len(hallazgos), "hallazgos": hallazgos, "skip": skip, "limit": limit}}


@mcp.tool(
    annotations=_SOLO_LECTURA,
    description=(
        "Consulta el detalle completo de un hallazgo OSINT concreto por su "
        "finding_id: incluye las señales de riesgo (top_flags) y el "
        "payload completo del análisis original, además de lo que ya trae "
        "el listado de listar_hallazgos_osint. No ejecuta ningún análisis "
        "nuevo. Si no existe ningún hallazgo con ese id, lo indica "
        "explícitamente."
    )
)
async def consultar_hallazgo_osint(finding_id: int) -> dict:
    if finding_id <= 0:
        raise ToolError("finding_id debe ser un entero positivo.")

    response = await _peticion_segura(
        "GET", f"/osint-findings/{finding_id}", client=osint_client, backend="OSINT"
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún hallazgo con id={finding_id}."),
        }

    if response.status_code != 200:
        raise ToolError(
            f"OSINT ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: recalcula la cronología (timeline) de un caso de "
        "Nexus desde cero — borra la cronología actual y la reconstruye a "
        "partir de las evidencias, eventos de tracking y hallazgos OSINT "
        "del caso. Requiere confirmado=true explícito: con confirmado=false "
        "(o sin indicarlo) se rechaza sin realizar ninguna petición al "
        "backend. No borra ni modifica evidencias, eventos de tracking ni "
        "hallazgos OSINT — son la fuente que se lee, nunca lo que se "
        "toca — solo la tabla derivada timeline_events de ESE caso. "
        "Úsala solo cuando el usuario pida explícitamente recalcular, "
        "refrescar o actualizar la cronología de un caso, nunca de forma "
        "automática ni especulativa."
    )
)
async def recalcular_cronologia(case_id: int, confirmado: bool) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    # Comprobado ANTES de tocar la red, a propósito: con confirmado=False
    # esta tool no debe generar ningún tráfico HTTP en absoluto, ni
    # siquiera de lectura — ver Fase MCP 2F.
    if not confirmado:
        raise ToolError(
            "recalcular_cronologia MODIFICA datos: borra y reconstruye la cronología del "
            "caso indicado. Requiere confirmado=true explícito. No se ha realizado ninguna "
            "petición al backend."
        )

    response = await _peticion_segura(
        "POST", f"/timeline/cases/{case_id}/refresh", client=timeline_client, backend="Timeline"
    )

    if response.status_code != 200:
        raise ToolError(
            f"Timeline ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    eventos = response.json()
    return {"estado": "ok", "datos": {"total": len(eventos), "eventos": eventos}}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: crea un caso nuevo en Nexus. Requiere confirmado=true "
        "explícito: con confirmado=false (o sin indicarlo) se rechaza sin "
        "realizar ninguna petición al backend. nombre y responsable son "
        "obligatorios; descripcion es opcional; estado es opcional y por "
        "defecto queda 'abierto' si no se indica (valores válidos: abierto, "
        "en_progreso, cerrado, archivado). Úsala solo cuando el usuario pida "
        "explícitamente crear o dar de alta un caso nuevo, nunca de forma "
        "automática ni especulativa."
    )
)
async def crear_caso(
    nombre: str,
    responsable: str,
    confirmado: bool,
    descripcion: str | None = None,
    estado: str | None = None,
) -> dict:
    if not nombre.strip():
        raise ToolError("nombre no puede estar vacío.")
    if not responsable.strip():
        raise ToolError("responsable no puede estar vacío.")
    if estado is not None and estado not in _ESTADOS_VALIDOS:
        raise ToolError(f"estado debe ser uno de {sorted(_ESTADOS_VALIDOS)}, no {estado!r}.")

    # Comprobado ANTES de tocar la red, a propósito: con confirmado=False
    # esta tool no debe generar ningún tráfico HTTP en absoluto — mismo
    # mecanismo que recalcular_cronologia (Fase 2F).
    if not confirmado:
        raise ToolError(
            "crear_caso MODIFICA datos: da de alta un caso nuevo en Nexus. Requiere "
            "confirmado=true explícito. No se ha realizado ninguna petición al backend."
        )

    payload: dict[str, object] = {"nombre": nombre, "responsable": responsable, "descripcion": descripcion}
    if estado is not None:
        payload["estado"] = estado

    response = await _peticion_segura("POST", "/cases", json=payload)

    if response.status_code != 201:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: cambia el estado de un caso existente (abierto, "
        "en_progreso, cerrado o archivado). Requiere confirmado=true "
        "explícito: con confirmado=false (o sin indicarlo) se rechaza sin "
        "realizar ninguna petición al backend. No todas las transiciones "
        "están permitidas (p. ej. un caso archivado es terminal e "
        "inmutable): si la transición no es válida, o el caso está "
        "eliminado o ya archivado, se indica explícitamente el motivo real "
        "en vez de un error genérico. Úsala solo cuando el usuario pida "
        "explícitamente cambiar el estado de un caso."
    )
)
async def cambiar_estado_caso(case_id: int, nuevo_estado: str, confirmado: bool) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if nuevo_estado not in _ESTADOS_VALIDOS:
        raise ToolError(f"nuevo_estado debe ser uno de {sorted(_ESTADOS_VALIDOS)}, no {nuevo_estado!r}.")

    if not confirmado:
        raise ToolError(
            "cambiar_estado_caso MODIFICA datos: cambia el estado del caso indicado. "
            "Requiere confirmado=true explícito. No se ha realizado ninguna petición al backend."
        )

    response = await _peticion_segura("PUT", f"/cases/{case_id}", json={"estado": nuevo_estado})

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id}."),
        }
    if response.status_code == 409:
        # Caso eliminado, caso archivado (terminal), o transición de estado no
        # permitida (ver backend/app/modules/cases/state_machine.py) — los
        # tres son el mismo HTTP 409 con `detail` distinto: se propaga el
        # mensaje real en vez de inventar una distinción que el backend no da.
        return {
            "estado": "conflicto",
            "detalle": _detalle_backend(response, "El cambio de estado no es posible en este momento."),
        }
    if response.status_code != 200:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: vincula un hallazgo OSINT existente (finding_id, ver "
        "listar_hallazgos_osint/consultar_hallazgo_osint) a un caso de Nexus "
        "(case_id). Requiere confirmado=true explícito: con confirmado=false "
        "(o sin indicarlo) se rechaza sin realizar ninguna petición al "
        "backend. Solo vincula — no admite desvincular (case_id nulo) ni "
        "borrar nada. Si el hallazgo no existe, o el caso destino no existe "
        "o está eliminado, se indica explícitamente en vez de inventar un "
        "resultado. Si el hallazgo ya estaba vinculado a ese mismo caso, la "
        "operación no hace nada (datos.cambiado=false) y no es un error. "
        "Úsala solo cuando el usuario pida explícitamente vincular, asociar "
        "o adjuntar un hallazgo OSINT a un caso."
    )
)
async def vincular_hallazgo(finding_id: int, case_id: int, confirmado: bool) -> dict:
    if finding_id <= 0:
        raise ToolError("finding_id debe ser un entero positivo.")
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")

    # Comprobado ANTES de tocar la red, a propósito: ni siquiera la lectura
    # que resuelve case_type/source_id del hallazgo debe ocurrir con
    # confirmado=False — mismo invariante "cero peticiones HTTP" que las
    # demás tools de escritura de esta fase.
    if not confirmado:
        raise ToolError(
            "vincular_hallazgo MODIFICA datos: asocia el hallazgo indicado al caso indicado. "
            "Requiere confirmado=true explícito. No se ha realizado ninguna petición al backend."
        )

    hallazgo_resp = await _peticion_segura(
        "GET", f"/osint-findings/{finding_id}", client=osint_client, backend="OSINT"
    )
    if hallazgo_resp.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(hallazgo_resp, f"No existe ningún hallazgo con id={finding_id}."),
        }
    if hallazgo_resp.status_code != 200:
        raise ToolError(
            f"OSINT ha respondido con un estado HTTP inesperado ({hallazgo_resp.status_code}): "
            f"{hallazgo_resp.text}"
        )

    hallazgo = hallazgo_resp.json()
    # `case_type`/`source_id` (no `finding_id`) son las claves que espera el
    # endpoint de vinculación: identifica la investigación de origen
    # (p. ej. ip_cases#4), no la fila de la vista consolidada osint_findings.
    case_type = hallazgo["case_type"]
    source_id = hallazgo["source_id"]

    vinculo_resp = await _peticion_segura(
        "PATCH",
        f"/osint-cases/{case_type}/{source_id}/vinculacion",
        client=osint_client,
        backend="OSINT",
        json={"case_id": case_id},
    )
    if vinculo_resp.status_code == 404:
        # Cubre tanto "no existe la investigación" (carrera improbable tras
        # el GET anterior) como "no existe el caso destino, o está
        # eliminado" (backend/app/modules/osint/case_link/service.py) — el
        # mensaje real de `detail` ya distingue cuál de los dos fue.
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(vinculo_resp, "No se ha podido vincular: revisa hallazgo y caso destino."),
        }
    if vinculo_resp.status_code != 200:
        raise ToolError(
            f"OSINT ha respondido con un estado HTTP inesperado ({vinculo_resp.status_code}): "
            f"{vinculo_resp.text}"
        )

    return {"estado": "ok", "datos": vinculo_resp.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: registra una evidencia nueva en un caso de Nexus "
        "(tipo, valor y opcionalmente observaciones/fecha_adquisicion). "
        "Requiere confirmado=true explícito: con confirmado=false (o sin "
        "indicarlo) se rechaza sin realizar ninguna petición al backend. "
        "tipo y valor son el contenido probatorio y quedan INMUTABLES tras "
        "crearse — el backend no permite editarlos después, solo "
        "observaciones/fecha_adquisicion (ver consultar_evidencia). El hash "
        "de integridad (SHA-256 de valor) lo calcula el backend "
        "automáticamente al crear: esta tool nunca lo calcula ni lo envía. "
        "Úsala solo cuando el usuario pida explícitamente registrar, añadir "
        "o dar de alta una evidencia nueva."
    )
)
async def registrar_evidencia(
    case_id: int,
    tipo: str,
    valor: str,
    confirmado: bool,
    observaciones: str | None = None,
    fecha_adquisicion: str | None = None,
) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if not tipo.strip():
        raise ToolError("tipo no puede estar vacío.")
    if len(tipo) > 50:
        raise ToolError(
            f"tipo no puede superar 50 caracteres (columna evidences.tipo VARCHAR(50)); "
            f"tiene {len(tipo)}."
        )
    if not valor.strip():
        raise ToolError("valor no puede estar vacío.")

    # Comprobado ANTES de tocar la red, a propósito: mismo mecanismo que las
    # demás tools de escritura de esta fase.
    if not confirmado:
        raise ToolError(
            "registrar_evidencia MODIFICA datos: crea una evidencia nueva (inmutable tras "
            "crearse) en el caso indicado. Requiere confirmado=true explícito. No se ha "
            "realizado ninguna petición al backend."
        )

    payload = {
        "tipo": tipo,
        "valor": valor,
        "observaciones": observaciones,
        "fecha_adquisicion": fecha_adquisicion,
    }
    response = await _peticion_segura("POST", f"/cases/{case_id}/evidences", json=payload)

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id}."),
        }
    if response.status_code == 409:
        # Caso eliminado lógicamente (backend/app/modules/cases/service.py::
        # create_evidence): un caso ARCHIVADO, en cambio, SÍ admite evidencia
        # nueva hoy — verificado en el código real, no es una omisión de esta
        # tool (create_evidence solo llama a get_active_case, que comprueba
        # `eliminado`, nunca `estado == archivado`).
        return {
            "estado": "conflicto",
            "detalle": _detalle_backend(response, "No se puede añadir la evidencia en este momento."),
        }
    if response.status_code != 201:
        raise ToolError(
            f"Casos ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos: persiste un conjunto de eventos de tracking ya "
        "clasificados (hora, evento, severidad, usuario_detectado opcional) "
        "en tracking_events de un caso de Nexus. NO analiza ningún log "
        "(eso es /analyze, fuera de esta tool): los eventos ya deben venir "
        "clasificados por quien llama. Requiere confirmado=true explícito: "
        "con confirmado=false (o sin indicarlo) se rechaza sin realizar "
        "ninguna petición al backend. Valida la estructura de cada evento y "
        "el volumen del array (máximo "
        f"{_MAX_EVENTOS_TRACKING_POR_LLAMADA} por llamada) antes de enviar "
        "nada. Úsala solo cuando el usuario pida explícitamente guardar o "
        "persistir eventos de tracking ya revisados."
    )
)
async def guardar_eventos_tracking(
    case_id: int,
    fuente_log: str,
    eventos: list[dict],
    confirmado: bool,
    sha256_log: str | None = None,
    forzar: bool = False,
) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if not fuente_log.strip() or len(fuente_log) > 100:
        raise ToolError("fuente_log debe ser texto no vacío de máximo 100 caracteres.")
    if not eventos:
        raise ToolError("eventos no puede estar vacío: no hay nada que guardar.")
    if len(eventos) > _MAX_EVENTOS_TRACKING_POR_LLAMADA:
        raise ToolError(
            f"eventos trae {len(eventos)} elementos; esta tool no envía más de "
            f"{_MAX_EVENTOS_TRACKING_POR_LLAMADA} de una vez (límite propio de esta tool, no "
            "del backend: evita una petición desproporcionada por error)."
        )
    if sha256_log is not None and not re.fullmatch(r"[0-9a-f]{64}", sha256_log):
        raise ToolError("sha256_log debe ser un hash SHA-256 en hexadecimal minúscula (64 caracteres), o None.")

    for i, evento in enumerate(eventos):
        if not isinstance(evento, dict):
            raise ToolError(f"eventos[{i}] debe ser un objeto, no {type(evento).__name__}.")
        if not evento.get("hora"):
            raise ToolError(f"eventos[{i}] no trae 'hora' (obligatorio).")
        if not isinstance(evento.get("evento"), str) or not evento["evento"].strip():
            raise ToolError(f"eventos[{i}] no trae 'evento' (obligatorio, texto no vacío).")
        severidad = evento.get("severidad")
        if severidad not in _SEVERIDADES_TRACKING_VALIDAS:
            raise ToolError(
                f"eventos[{i}].severidad debe ser una de {sorted(_SEVERIDADES_TRACKING_VALIDAS)}, "
                f"no {severidad!r}."
            )
        usuario = evento.get("usuario_detectado")
        if usuario is not None and (not isinstance(usuario, str) or len(usuario) > 100):
            raise ToolError(f"eventos[{i}].usuario_detectado debe ser texto de máximo 100 caracteres.")

    # Comprobado ANTES de tocar la red, a propósito: mismo mecanismo que las
    # demás tools de escritura de esta fase.
    if not confirmado:
        raise ToolError(
            "guardar_eventos_tracking MODIFICA datos: persiste eventos nuevos en tracking_events "
            "del caso indicado. Requiere confirmado=true explícito. No se ha realizado ninguna "
            "petición al backend."
        )

    payload = {
        "case_id": case_id,
        "fuente_log": fuente_log,
        "eventos": eventos,
        "sha256_log": sha256_log,
        "forzar": forzar,
    }
    response = await _peticion_segura(
        "POST",
        f"/cases/{case_id}/tracking/events",
        client=tracking_client,
        backend="Tracking",
        json=payload,
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id}."),
        }
    if response.status_code == 409:
        # Caso eliminado/archivado (CasoNoModificableError), o este mismo
        # fichero de log ya se guardó en el caso (LogYaGuardadoError) —
        # mismo HTTP 409, `detail` distinto; se propaga el mensaje real en
        # vez de inventar una distinción.
        return {
            "estado": "conflicto",
            "detalle": _detalle_backend(response, "No se han podido guardar los eventos en este momento."),
        }
    if response.status_code != 200:
        raise ToolError(
            f"Tracking ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos y tiene COSTE ECONÓMICO REAL: genera un informe "
        "pericial nuevo y completo de un caso mediante IA (resumen y "
        "conclusiones a partir de evidencias, tracking, OSINT y cronología). "
        "Requiere confirmado=true explícito: con confirmado=false (o sin "
        "indicarlo) se rechaza sin realizar ninguna petición al backend — "
        "NUNCA la ejecutes sin confirmación explícita del usuario, por el "
        "coste y el tiempo que implica. Emite el informe COMPLETO del caso "
        "(los tres anexos, los cuatro formatos): esta tool no expone el "
        "alcance parcial que sí admite el endpoint real (fechas, anexos o "
        "formatos concretos). No descarga ningún fichero: solo genera el "
        "registro del informe y devuelve sus metadatos — usa "
        "consultar_informe/listar_informes_de_caso para consultarlo después. "
        "Úsala solo cuando el usuario pida explícitamente generar o emitir "
        "un informe nuevo, nunca de forma automática ni especulativa."
    )
)
async def generar_informe(
    case_id: int, generado_por: str, confirmado: bool, notas: str | None = None
) -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if not generado_por.strip():
        raise ToolError("generado_por no puede estar vacío.")
    if len(generado_por) > 100:
        raise ToolError(f"generado_por no puede superar 100 caracteres; tiene {len(generado_por)}.")

    # Comprobado ANTES de tocar la red, a propósito: esta tool dispara una
    # llamada real a un modelo de IA (coste económico, tiempo) — el
    # mecanismo de confirmado es el mismo que las demás tools de escritura,
    # pero aquí la razón de exigirlo es doblemente importante.
    if not confirmado:
        raise ToolError(
            "generar_informe MODIFICA datos y tiene COSTE ECONÓMICO REAL (llamada a un modelo "
            "de IA): genera un informe nuevo del caso indicado. Requiere confirmado=true "
            "explícito. No se ha realizado ninguna petición al backend."
        )

    response = await _peticion_segura(
        "POST",
        "/reports/generate",
        client=informes_client,
        backend="Informes",
        json={"case_id": case_id, "generado_por": generado_por, "notas": notas},
        # Los 5 clientes comparten un timeout fijo de 10s (app/core/
        # http_client.py), pensado para peticiones CRUD normales — esta es
        # la única llamada del MCP Server que hace de verdad una llamada a
        # un modelo de IA (segundos reales, no milisegundos), así que
        # necesita más margen; httpx acepta un timeout por petición que
        # sustituye, solo aquí, al del cliente.
        timeout=120.0,
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id}."),
        }
    if response.status_code == 409:
        # VersionConflictError (sharingan/app/modules/reports/routes.py):
        # dos generaciones simultáneas del mismo caso se pisaron el número
        # de versión — no es culpa de esta petición, reintentarla funciona
        # (así lo documenta el propio backend).
        return {
            "estado": "conflicto",
            "detalle": _detalle_backend(
                response,
                "Conflicto con otra generación simultánea del mismo caso; reintentar suele bastar.",
            ),
        }
    if response.status_code != 200:
        raise ToolError(
            f"Informes ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ANALISIS_SIN_PERSISTENCIA,
    description=(
        "Analiza un fichero de log LOCAL (auth.log, syslog, un export de "
        "comandos, etc.) y devuelve una vista previa clasificada — NO "
        "persiste nada, es un análisis puro (usa guardar_eventos_tracking "
        "para persistir eventos ya revisados). 'ruta' debe ser una ruta "
        "local dentro de uno de los directorios permitidos (ver "
        "MCP_ALLOWED_FILE_DIRS en mcp-server/.env); cualquier otra ruta, "
        "incluida vía '..' o un enlace simbólico, se rechaza antes de leer "
        "nada. No requiere confirmado: no modifica ningún dato. Úsala solo "
        "cuando el usuario pida explícitamente analizar o clasificar un "
        "fichero de log."
    )
)
async def analizar_log(case_id: int, ruta: str, zona_horaria: str = "UTC") -> dict:
    if case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo.")
    if not _ZONA_HORARIA_RE.match(zona_horaria.strip()):
        raise ToolError("zona_horaria debe ser 'UTC' o un desplazamiento como '+02:00'.")

    ruta_resuelta = _validar_ruta_permitida(ruta)

    contenido = ruta_resuelta.read_bytes()

    response = await _peticion_segura(
        "POST",
        f"/cases/{case_id}/tracking/analyze",
        client=tracking_client,
        backend="Tracking",
        files={"file": (ruta_resuelta.name, contenido, "text/plain")},
        data={"zona_horaria": zona_horaria},
        # Fichero local (hasta ~20MB) + clasificación CPU pura: más margen
        # que el timeout de 10s compartido, sin llegar a los 120s que sí
        # necesita generar_informe (llamada a IA, Fase 2H) — no hay red
        # externa aquí, solo lectura y regex.
        timeout=30.0,
    )

    if response.status_code == 404:
        return {
            "estado": "no_encontrado",
            "detalle": _detalle_backend(response, f"No existe ningún caso con id={case_id}."),
        }
    if response.status_code == 409:
        return {
            "estado": "conflicto",
            "detalle": _detalle_backend(response, "El caso no admite eventos nuevos en este momento."),
        }
    if response.status_code == 400:
        # Zona horaria con forma válida pero fuera de rango, o el fichero no
        # se pudo decodificar como texto (`FicheroNoTextoError`) — el
        # `detail` real del backend no incluye contenido del fichero, solo
        # un motivo genérico.
        raise ToolError(
            f"Tracking ha rechazado el fichero o la zona horaria: {_detalle_backend(response, response.text)}"
        )
    if response.status_code == 413:
        raise ToolError(
            f"Tracking ha rechazado el fichero por tamaño (413): {_detalle_backend(response, response.text)}"
        )
    if response.status_code != 200:
        raise ToolError(
            f"Tracking ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


@mcp.tool(
    annotations=_ESCRITURA_DESTRUCTIVA,
    description=(
        "ESCRIBE datos, tiene efectos de red reales y puede consumir cuotas "
        "de APIs externas: ejecuta un análisis OSINT completo de un dominio "
        "(WHOIS, certificado SSL, VirusTotal, DNS, reputación de sus IPs en "
        "AbuseIPDB, subdominios vía crt.sh, historial en Wayback Machine) y "
        "PERSISTE el resultado como un hallazgo OSINT nuevo — por eso, a "
        "diferencia de analizar_log, sí requiere confirmado=true explícito: "
        "con confirmado=false (o sin indicarlo) se rechaza sin realizar "
        "ninguna petición al backend. Si alguna fuente externa falla, el "
        "análisis se completa igualmente con las demás (el propio backend "
        "lo señala en 'errors', sin ocultarlo). Úsala solo cuando el "
        "usuario pida explícitamente analizar un dominio, nunca de forma "
        "automática ni especulativa (cada llamada es una consulta real a "
        "varios servicios externos)."
    )
)
async def analizar_dominio(domain: str, confirmado: bool, case_id: int | None = None) -> dict:
    if not domain.strip():
        raise ToolError("domain no puede estar vacío.")
    if case_id is not None and case_id <= 0:
        raise ToolError("case_id debe ser un entero positivo si se indica.")

    if not confirmado:
        raise ToolError(
            "analizar_dominio MODIFICA datos (persiste un hallazgo OSINT nuevo) y tiene efectos "
            "de red reales (VirusTotal, AbuseIPDB, WHOIS, crt.sh, Wayback Machine). Requiere "
            "confirmado=true explícito. No se ha realizado ninguna petición al backend."
        )

    response = await _peticion_segura(
        "POST",
        "/analysis/domain",
        client=osint_client,
        backend="OSINT",
        json={"domain": domain, "case_id": case_id},
        # Varias fuentes externas encadenadas (WHOIS, SSL, VirusTotal, DNS,
        # AbuseIPDB, crt.sh, Wayback): más lento que una petición normal,
        # aunque no tanto como una llamada a IA (generar_informe, 120s).
        timeout=60.0,
    )

    if response.status_code != 200:
        raise ToolError(
            f"OSINT ha respondido con un estado HTTP inesperado ({response.status_code}): {response.text}"
        )

    return {"estado": "ok", "datos": response.json()}


if __name__ == "__main__":
    mcp.run(transport="stdio")
