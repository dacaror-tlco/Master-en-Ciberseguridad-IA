"""
Esquemas Pydantic del Módulo 3 (I/O de la API). Reflejan únicamente el
modelo oficial de CLAUDE.md — no exponen nada de la cadena de hashes
interna (ver chain_integrity.py).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Severidad

MAX_BYTES_EVENTO = 65535


class TrackingEventOut(BaseModel):
    """Lo que la API devuelve al consultar eventos de tracking."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    hora: datetime
    """En UTC. La columna no guarda zona, así que se marca aquí: sin ella el
    navegador leía `03:11:19` como hora local y la desplazaba respecto a la
    vista previa."""
    evento: str
    severidad: Severidad
    fuente_log: str | None = None
    usuario_detectado: str | None = None

    # --- procedencia (no son columnas de tracking_events) ---
    # Se conservan en la cadena de integridad local. Ambos a None significa
    # que ese dato no está disponible para este evento, no que no hubiera
    # regla: p. ej. filas insertadas por fuera de la aplicación.
    regla: str | None = None
    hora_inferida: bool | None = None

    @field_validator("hora")
    @classmethod
    def _hora_en_utc(cls, hora: datetime) -> datetime:
        # tracking_events.hora se guarda siempre en UTC sin zona (ver tiempo.py)
        return hora.replace(tzinfo=timezone.utc) if hora.tzinfo is None else hora.astimezone(timezone.utc)


# Valores cerrados: se publican en OpenAPI como enum, para que quien consuma
# la API (Timeline, Correlation Engine, el frontend) sepa que esperar sin
# leer el codigo del extractor.
TipoIndicador = Literal["ip_publica", "ip_privada", "dominio", "url", "ruta", "hash", "email"]
OrigenIndicador = Literal["comando", "salida", "decodificado"]


class IndicadorOut(BaseModel):
    """Un indicador extraído de un evento, con su procedencia."""
    tipo: TipoIndicador
    valor: str
    origen: OrigenIndicador


class IndicadorAgregado(BaseModel):
    """El mismo indicador, visto en todo el log.

    Es la vista que sirve para seguir al atacante: una IP que aparece en seis
    comandos distintos importa más que una que aparece en uno, y saber en qué
    líneas aparece permite ir directo a ellas.
    """
    tipo: TipoIndicador
    valor: str
    veces: int
    lineas: list[int]
    severidad_maxima: Severidad


class AnalyzePreviewItem(BaseModel):
    """Una fila de la vista previa de análisis (todavía no persistida).

    Los campos de detalle son opcionales a propósito: el frontend los usa
    para el panel lateral, pero `SaveEventsRequest` reutiliza este mismo
    modelo, así que un cliente puede devolver solo lo que se persiste.
    Ninguno de ellos llega a `tracking_events` — el esquema oficial de
    CLAUDE.md no cambia.
    """
    hora: datetime
    evento: str = Field(min_length=1)
    severidad: Severidad
    # Límites de las columnas de tracking_events. Sin validarlos, SQLite los
    # aceptaba y MySQL respondía 500 (o truncaba) al guardar.
    usuario_detectado: str | None = Field(default=None, max_length=100)
    regla: str | None = None
    """Regla que decide la severidad: la más grave de las que casaron."""
    reglas: list[str] = []
    """Todas las reglas que casaron, en el orden de rules.yaml."""
    mitre: list[str] = []
    """Técnicas MITRE ATT&CK de las reglas que casaron (p. ej. T1059.001)."""

    # --- detalle para el panel del analista (no se persiste) ---
    linea_original: str | None = None   # la línea tal cual venía en el log
    numero_linea: int | None = None     # su posición dentro del fichero
    hora_inferida: bool = False         # True si la línea no traía timestamp
    regla_descripcion: str | None = None  # por qué ese patrón es sospechoso
    indicadores: list[IndicadorOut] = []
    """Indicadores extraídos del comando y de su salida (IPs, dominios, URLs,
    rutas, hashes, correos). No se persisten: `tracking_events` mantiene el
    esquema de CLAUDE.md. Viajan aquí para que Timeline, Correlation Engine o
    IOC Intelligence no tengan que reparsear el texto del evento."""

    comando_decodificado: str | None = None
    """Lo que esconde un `powershell -EncodedCommand` (base64 UTF-16LE), ya
    legible. Solo se decodifica: nunca se ejecuta."""

    salida: str | None = None
    """Salida que produjo el comando.

    Se rellena con las líneas indentadas que el log traiga bajo el comando
    (ver `log_parser`). No todos los comandos producen salida. NUNCA se
    obtiene ejecutando el comando — son comandos extraídos de un incidente
    real y ejecutarlos destruiría la máquina de análisis.
    """

    @field_validator("evento")
    @classmethod
    def _evento_cabe_en_text(cls, evento: str) -> str:
        # tracking_events.evento es TEXT: en MySQL, 65.535 BYTES (no caracteres)
        if len(evento.encode("utf-8")) > MAX_BYTES_EVENTO:
            raise ValueError(f"el evento supera {MAX_BYTES_EVENTO} bytes, el máximo de la columna")
        return evento


class AnalyzeLogResponse(BaseModel):
    """Respuesta al analizar un log: preview de lo detectado, sin guardar."""
    total_eventos: int
    por_severidad: dict[str, int]
    eventos: list[AnalyzePreviewItem]
    indicadores: list[IndicadorAgregado] = []
    """Todos los indicadores del log, agrupados por valor y ordenados por
    severidad máxima y número de apariciones: lo primero que el perito
    querría mirar."""
    codificacion: str | None = None
    """Codificación con la que se leyó el fichero (utf-8, utf-8-sig, utf-16,
    cp1252...). Parte de la procedencia: dice cómo se interpretaron los bytes."""
    sha256_log: str | None = None
    """SHA-256 del fichero tal cual se subió. Identifica el log: permite avisar
    de que ya se guardó en el caso y queda como procedencia en la cadena local."""
    eventos_ya_guardados: int = 0
    """Eventos de este mismo fichero (mismo SHA-256) ya guardados en el caso.
    Si es mayor que 0, guardarlo otra vez duplicaría los eventos."""


class SaveEventsRequest(BaseModel):
    """Lo que el frontend reenvía para persistir tras revisar el preview."""
    case_id: int
    fuente_log: str = Field(min_length=1, max_length=100)
    eventos: list[AnalyzePreviewItem]
    sha256_log: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    """El `sha256_log` del análisis. Con él, guardar dos veces el mismo log en
    el mismo caso se rechaza (409) salvo que se pida con `forzar`."""
    forzar: bool = False


class SaveEventsResponse(BaseModel):
    guardados: int
    tracking_events: list[TrackingEventOut]


class CaseOption(BaseModel):
    """
    Lo mínimo para el selector de caso del frontend (id, nombre, estado).
    Se lee directo de la tabla compartida `cases` (ver repository.py) — no
    es un import del modelo de Casos, es una proyección propia de este
    backend sobre una tabla que no posee.
    """
    id: int
    nombre: str
    estado: str


class VerifyIntegrityResponse(BaseModel):
    """
    Resultado de la verificación de integridad interna. Deliberadamente
    NO incluye hashes ni ningún detalle de la cadena — solo un veredicto,
    un mensaje y qué eventos no cuadran, para no filtrar la capa interna
    al contrato de la API.
    """
    ok: bool
    mensaje: str
    problemas: list[str] = []
    """Eventos de `tracking_events` que no coinciden con lo guardado:
    modificados, borrados o insertados por fuera de la aplicación."""
