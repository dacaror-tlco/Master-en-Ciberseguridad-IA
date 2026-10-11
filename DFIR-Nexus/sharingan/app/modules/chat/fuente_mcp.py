"""
El expediente del asistente, leído a través del servidor MCP de Nexus.

Sustituye a las consultas SQL directas de `context.construir` cuando
`CHAT_CONTEXTO=mcp`. El asistente deja de tener acceso a la base: todo lo que
sabe del caso llega por los endpoints de los cinco módulos, a través del
MCP (`mcp-server/`), igual que le llegaría a cualquier otro cliente.

Lo que **no** cambia, y es deliberado: **el modelo sigue sin herramientas.**
Quien llama al MCP es este código, con el `case_id` de la petición fijado
aquí. Si el modelo pudiera llamar a las herramientas, elegiría él qué caso
consulta, y el aislamiento entre casos —la defensa que resistió los siete
ataques de la batería de inyección del caso #22— pasaría a depender de que
obedezca al prompt. Un agente con herramientas tiene más acceso que un
redactor sin ellas, no menos.

Dos decisiones más:

* **Identidad del analista, no de servicio.** El proceso MCP se lanza con el
  JWT de quien pregunta (`MCP_ACCESS_TOKEN`), así que el asistente no puede
  leer nada que ese analista no pueda leer, y la lectura queda a su nombre.
* **Un proceso por pregunta, por stdio.** El MCP no escucha en ningún puerto:
  vive dentro de este contenedor el tiempo que dura la lectura. Cuesta un
  arranque de Python por pregunta (del orden de un segundo, frente a decenas
  de la respuesta del modelo) y a cambio no hay un servicio más expuesto en
  la red, con herramientas de escritura, al que alguien pudiera hablarle.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings
from app.modules.reports.osint import FuenteOsint, RegistroOsint, desde_osint_finding

#: Las únicas herramientas que este módulo llama. Todas de solo lectura; el
#: resto del servidor (crear casos, emitir informes…) no se toca nunca desde
#: aquí.
HERRAMIENTAS = (
    "consultar_caso",
    "listar_evidencias_de_caso",
    "listar_hallazgos_osint",
    "listar_eventos_tracking",
    "obtener_cronologia_caso",
    "listar_informes_de_caso",
)

#: Variables que el proceso MCP necesita, y ninguna más. No hereda el entorno
#: de Informes: ahí están la clave de Anthropic y la cadena de conexión a la
#: base, que el MCP no necesita para nada.
_URLS = ("CASOS_BASE_URL", "OSINT_BASE_URL", "TRACKING_BASE_URL", "TIMELINE_BASE_URL", "INFORMES_BASE_URL")

#: Lo que devuelve `GET /cases/{id}/evidences` como máximo sin paginar.
_LIMITE_EVIDENCIAS_API = 100


class FuenteMcpError(Exception):
    """El MCP no ha podido leer el expediente. El mensaje es apto para el perito."""


def construir(case_id: int, token: str):
    """El `ContextoCaso` del caso leído por MCP, o `None` si el caso no existe."""
    from app.modules.chat import context  # import diferido: context no depende de este módulo

    datos = asyncio.run(_leer(case_id, token))
    if datos is None:
        return None
    return context.armar(**datos)


async def _leer(case_id: int, token: str) -> dict[str, Any] | None:
    try:
        async with stdio_client(_parametros(token)) as (lectura, escritura):
            async with ClientSession(lectura, escritura) as sesion:
                await sesion.initialize()
                return await _expediente(sesion, case_id)
    except FuenteMcpError:
        raise
    except Exception as exc:  # proceso que no arranca, transporte roto…
        raise FuenteMcpError(
            f"No se ha podido leer el expediente a través del servidor MCP: {exc}"
        ) from exc


async def _expediente(sesion: ClientSession, case_id: int) -> dict[str, Any] | None:
    caso = await _llamar(sesion, "consultar_caso", case_id=case_id)
    if not caso.get("encontrado"):
        return None

    # Las cinco lecturas son independientes: en paralelo, sobre la misma sesión.
    evidencias, hallazgos, tracking, cronologia, informes = await asyncio.gather(
        _listar(sesion, "listar_evidencias_de_caso", "evidencias", case_id=case_id),
        _listar(sesion, "listar_hallazgos_osint", "hallazgos", case_id=case_id, limit=200),
        _listar(sesion, "listar_eventos_tracking", "eventos", case_id=case_id, limit=1000),
        _listar(sesion, "obtener_cronologia_caso", "eventos", case_id=case_id),
        _listar(sesion, "listar_informes_de_caso", "informes", case_id=case_id),
    )

    avisos: list[str] = []
    if len(evidencias) >= _LIMITE_EVIDENCIAS_API:
        avisos.append(
            f"Evidencias: la API devuelve como máximo {_LIMITE_EVIDENCIAS_API} por consulta. "
            "Puede haber más que el asistente no ha visto."
        )

    # Mismo orden que las consultas SQL de `reports/repository.py`: la
    # numeración de las citas (EV1, TR3…) tiene que ser la misma lea de donde lea.
    return {
        "case": _caso(caso["caso"]),
        "evidencias": sorted(map(_evidencia, evidencias), key=lambda e: (e.fecha_subida, e.id)),
        "registro": RegistroOsint(
            indicadores=[
                desde_osint_finding(h)
                for h in sorted(map(_hallazgo, hallazgos), key=lambda h: (h.analyzed_at, h.id))
            ],
            fuente=FuenteOsint.FINDINGS,
        ),
        "tracking": sorted(map(_evento_tracking, tracking), key=lambda t: (t.hora, t.id)),
        "cronologia": sorted(map(_cronologia, cronologia), key=lambda t: (t.orden, t.fecha_hora, t.id)),
        "informes": sorted(map(_informe, informes), key=lambda i: (i.version, i.id)),
        "avisos": avisos,
    }


async def _llamar(sesion: ClientSession, herramienta: str, **argumentos: Any) -> dict:
    assert herramienta in HERRAMIENTAS, herramienta
    resultado = await sesion.call_tool(herramienta, argumentos)
    texto = "".join(getattr(b, "text", "") for b in resultado.content)
    if resultado.isError:
        raise FuenteMcpError(f"El servidor MCP ha fallado en {herramienta}: {texto[:300]}")
    return json.loads(texto)


async def _listar(sesion: ClientSession, herramienta: str, clave: str, **argumentos: Any) -> list[dict]:
    """Las herramientas de listado devuelven `ok`, `sin_resultados` o `no_encontrado`."""
    respuesta = await _llamar(sesion, herramienta, **argumentos)
    if respuesta.get("estado") == "ok":
        return respuesta["datos"][clave]
    return []


def _parametros(token: str) -> StdioServerParameters:
    entorno = {var: os.environ[var] for var in _URLS if var in os.environ}
    entorno["MCP_ACCESS_TOKEN"] = token
    directorio = Path(settings.chat_mcp_dir).resolve()
    return StdioServerParameters(
        command=settings.chat_mcp_python or sys.executable,
        args=["-m", "app.main"],
        cwd=directorio,
        env=entorno,
    )


# -- de JSON a objetos con los atributos de los modelos ORM -----------------


def _fecha(valor: str | None) -> datetime | None:
    """
    Fechas como las guarda la base: UTC y sin zona.

    Tracking las publica con zona (`+00:00`) y el resto sin ella. Es el mismo
    instante, pero el modelo tiene que ver el mismo texto lea de donde lea, y
    Python no deja ordenar fechas con y sin zona mezcladas.
    """
    if not valor:
        return None
    fecha = datetime.fromisoformat(valor)
    if fecha.tzinfo is not None:
        fecha = fecha.astimezone(timezone.utc).replace(tzinfo=None)
    return fecha


def _enum(valor: str) -> SimpleNamespace:
    """`context.py` lee `.value` de los Enum del ORM (`estado`, `severidad`)."""
    return SimpleNamespace(value=valor)


def _caso(c: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=c["id"],
        nombre=c["nombre"],
        estado=_enum(c["estado"]),
        responsable=c.get("responsable"),
        fecha_creacion=_fecha(c["fecha_creacion"]),
        descripcion=c.get("descripcion"),
    )


def _evidencia(e: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=e["id"],
        tipo=e["tipo"],
        valor=e["valor"],
        observaciones=e.get("observaciones"),
        fecha_subida=_fecha(e["fecha_subida"]),
    )


def _hallazgo(h: dict) -> SimpleNamespace:
    return SimpleNamespace(**{**h, "analyzed_at": _fecha(h["analyzed_at"])})


def _evento_tracking(t: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=t["id"],
        hora=_fecha(t["hora"]),
        severidad=_enum(t["severidad"]),
        usuario_detectado=t.get("usuario_detectado"),
        fuente_log=t.get("fuente_log"),
        evento=t["evento"],
    )


def _cronologia(t: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=t["id"],
        fecha_hora=_fecha(t["fecha_hora"]),
        origen_modulo=t["origen_modulo"],
        origen_id=t["origen_id"],
        descripcion=t["descripcion"],
        orden=t.get("orden") or 0,
    )


def _informe(i: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=i["id"],
        version=i["version"],
        fecha_generacion=_fecha(i["fecha_generacion"]),
        generado_por=i.get("generado_por"),
    )
