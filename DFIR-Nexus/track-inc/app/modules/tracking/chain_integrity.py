"""
Capa de integridad interna del Módulo 3.

DECISIÓN DE DISEÑO IMPORTANTE: CLAUDE.md marca la cadena de custodia /
hashes de integridad como "fuera de alcance por ahora" y pide
explícitamente no anticiparla en el modelo de datos oficial. Por eso
esta capa vive **completamente fuera** del esquema compartido:

  - No añade columnas a `tracking_events`.
  - No usa la base de datos MySQL compartida.
  - Persiste en un fichero SQLite local por caso, bajo
    `.tracking_chain/case_<id>.db`.
  - Nadie del resto del equipo necesita saber que existe para que su
    código funcione: es un extra interno de este módulo, no una
    dependencia del sistema.

QUÉ PROTEGE. Cada eslabón guarda la huella de una fila concreta de
`tracking_events` (su id y sus columnas tal y como quedaron en la base de
datos). Verificar hace dos comprobaciones, y hacen falta las dos:

  1. Que la cadena local no se ha tocado (hashes enlazados).
  2. Que `tracking_events` sigue coincidiendo con la cadena: ninguna fila
     modificada, borrada o insertada por fuera de la aplicación.

Antes solo se hacía la primera, y "Verificar integridad" respondía
"Cadena íntegra" aunque alguien hubiera editado o borrado eventos en la
base de datos: justo lo que se pretendía detectar.

Si en el futuro el equipo decide adoptar esto como parte oficial del
proyecto, migrar consiste en: (a) decidir si se expone vía API, y (b)
decidir si se traslada a MySQL — ninguna de las dos cosas afecta
al esquema actual de `tracking_events`.

Reutiliza el motor ya construido y testeado en `agent.evidence`.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.evidence.chain import ChainError, EvidenceChain, verify_chain
from agent.evidence.models import Criticality, EventSource, EvidenceRecord, HostInfo, RawEvent
from agent.evidence.store import EvidenceStore

from .tiempo import a_utc_sin_zona

# Ruta ABSOLUTA: antes era relativa al directorio desde el que se arrancaba
# el proceso, así que arrancar desde otra carpeta "perdía" las cadenas (y
# verificar decía que no había eventos) y `pytest` lanzado desde la raíz
# del módulo borraba las cadenas reales. TRACKING_CHAIN_DIR permite moverla
# (tests, volumen de Docker).
CHAIN_STORAGE_DIR = Path(
    os.environ.get("TRACKING_CHAIN_DIR")
    or Path(__file__).resolve().parents[3] / ".tracking_chain"
)

_HOST_INFO = HostInfo(agent_id="tracking-module", hostname="n/a", os="n/a")

# Los mensajes de ChainError citan hashes completos; la API no debe
# exponerlos (ver VerifyIntegrityResponse).
_RE_HEX_LARGO = re.compile(r"\b[0-9a-f]{64}\b")

# Límite de problemas que se devuelven en detalle: con miles de filas
# manipuladas basta con el recuento y los primeros casos.
MAX_PROBLEMAS = 50

_CAMPOS = ("case_id", "hora", "evento", "severidad", "fuente_log", "usuario_detectado")


def _db_path_for_case(case_id: int) -> Path:
    return CHAIN_STORAGE_DIR / f"case_{case_id}.db"


def hora_canonica(hora: datetime) -> str:
    """Hora en UTC, sin zona y a segundos: la forma exacta en que queda en
    `tracking_events`. Así la huella no depende de si llega con zona o de
    los microsegundos que la base de datos descarte."""
    return a_utc_sin_zona(hora).isoformat()


def huella_fila(fila: Any) -> dict[str, Any]:
    """Lo que se protege de una fila de `tracking_events`."""
    severidad = fila.severidad
    return {
        "tracking_event_id": fila.id,
        "case_id": fila.case_id,
        "hora": hora_canonica(fila.hora),
        "evento": fila.evento,
        "severidad": getattr(severidad, "value", severidad),
        "fuente_log": fila.fuente_log,
        "usuario_detectado": fila.usuario_detectado,
    }


def _registro_para(
    fila: Any, criticidad: Criticality, regla: str | None, hora_inferida: bool, sha256_log: str | None = None
) -> RawEvent:
    huella = huella_fila(fila)
    return RawEvent(
        source=EventSource.LOG,
        event_type="tracking_event",
        timestamp=datetime.fromisoformat(huella["hora"]).replace(tzinfo=timezone.utc),
        host_info=_HOST_INFO,
        # `regla`, `hora_inferida` y el SHA-256 del log de origen no caben en
        # tracking_events (esquema de CLAUDE.md), pero son parte de la
        # procedencia del evento: se conservan aquí, protegidos por la cadena.
        payload={
            "tracking_event": huella,
            "regla": regla,
            "hora_inferida": hora_inferida,
            "sha256_log": sha256_log,
        },
    )


def eventos_guardados_del_log(case_id: int, sha256_log: str) -> int:
    """Cuántos eventos de ese fichero de log (por su SHA-256) ya se guardaron
    en el caso. Sirve para avisar antes de duplicarlos."""
    db_path = _db_path_for_case(case_id)
    if not db_path.exists():
        return 0
    store = EvidenceStore(db_path)
    try:
        return sum(1 for r in store.get_all() if r.event.payload.get("sha256_log") == sha256_log)
    finally:
        store.close()


#: (fila de tracking_events, criticidad, regla que disparó, hora inferida)
FilaClasificada = tuple[Any, Criticality, str | None, bool]


def metadatos_por_evento(case_id: int) -> dict[int, dict[str, Any]]:
    """Regla y hora inferida de cada evento guardado, por id de
    `tracking_events`. Vacío si el caso no tiene cadena."""
    db_path = _db_path_for_case(case_id)
    if not db_path.exists():
        return {}
    store = EvidenceStore(db_path)
    try:
        records = store.get_all()
    finally:
        store.close()

    metadatos: dict[int, dict[str, Any]] = {}
    for record in records:
        payload = record.event.payload
        huella = payload.get("tracking_event")
        if huella is None:
            continue
        metadatos[huella["tracking_event_id"]] = {
            "regla": payload.get("regla"),
            "hora_inferida": bool(payload.get("hora_inferida", False)),
        }
    return metadatos


@contextmanager
def registro_atomico(
    case_id: int, sha256_log: str | None = None
) -> Iterator[Callable[[list[FilaClasificada]], list[EvidenceRecord]]]:
    """
    Abre la cadena del caso en exclusiva y entrega una función para añadir
    filas de `tracking_events` (ya con id, tras un flush). Lo añadido solo
    se confirma si el bloque termina sin error; si falla, se deshace.

    Uso en el guardado:

        with registro_atomico(case_id) as registrar:
            filas = crear filas + flush       # ids asignados, sin commit
            registrar([(fila, criticidad, regla, hora_inferida), ...])
            db.commit()                       # si falla, la cadena se deshace

    El orden importa. Antes se confirmaba la base de datos y DESPUÉS se
    escribía la cadena, sin exclusión entre peticiones: con varios guardados
    a la vez, la cadena fallaba, la API devolvía 500... y los eventos ya
    estaban guardados, así que el perito reintentaba y los duplicaba.
    """
    CHAIN_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(_db_path_for_case(case_id))
    try:
        with store.transaccion_exclusiva():
            last_hash, last_seq = store.get_last_hash_and_seq()
            chain = EvidenceChain(last_hash=last_hash, last_seq=last_seq)

            def registrar(filas: list[FilaClasificada]) -> list[EvidenceRecord]:
                records: list[EvidenceRecord] = []
                for fila, criticidad, regla, hora_inferida in filas:
                    record = chain.append(
                        _registro_para(fila, criticidad, regla, hora_inferida, sha256_log),
                        criticidad,
                        matched_rule=regla,
                    )
                    store.append(record, commit=False)
                    records.append(record)
                return records

            yield registrar
    finally:
        store.close()


def verify_case_chain(case_id: int, filas_bd: list[Any]) -> tuple[bool, str, list[str]]:
    """
    Verifica la cadena local de un caso Y la compara con sus filas actuales
    de `tracking_events`. Devuelve (ok, mensaje, problemas).
    """
    db_path = _db_path_for_case(case_id)
    records: list[EvidenceRecord] = []
    if db_path.exists():
        store = EvidenceStore(db_path)
        try:
            records = store.get_all()
        finally:
            store.close()

    if not records and not filas_bd:
        return True, "No hay eventos de tracking registrados todavía para este caso.", []

    if not records:
        # Hay eventos en tracking_events pero ninguna cadena para el caso. Lo
        # habitual no es una manipulación sino un despliegue sin volumen
        # persistente para la cadena (TRACKING_CHAIN_DIR): cada redespliegue
        # la pierde. Se dice explícitamente, en vez de listar cada evento como
        # "insertado por fuera", que sugiere un ataque que no ha ocurrido.
        return (
            False,
            f"No se encuentra la cadena de integridad de este caso, pero tracking_events tiene "
            f"{len(filas_bd)} evento(s): no se puede verificar. Si la aplicación se ha redesplegado, "
            f"revisa que la carpeta de la cadena ({CHAIN_STORAGE_DIR}) esté en un volumen persistente.",
            [],
        )

    try:
        verify_chain(records)
    except ChainError as e:
        detalle = _RE_HEX_LARGO.sub("…", str(e))
        return False, f"Cadena comprometida: el registro local de integridad fue manipulado ({detalle}).", []

    en_cadena: dict[int, dict[str, Any]] = {}
    problemas: list[str] = []
    for record in records:
        huella = record.event.payload.get("tracking_event")
        if huella is None:
            problemas.append(
                f"Registro seq={record.seq}: formato antiguo, sin vínculo a una fila de tracking_events."
            )
            continue
        en_cadena[huella["tracking_event_id"]] = huella

    en_bd = {fila.id: huella_fila(fila) for fila in filas_bd}

    for event_id in sorted(en_cadena.keys() - en_bd.keys()):
        problemas.append(f"Evento #{event_id}: se guardó pero ya no está en tracking_events (borrado).")
    for event_id in sorted(en_cadena.keys() & en_bd.keys()):
        cambiados = [c for c in _CAMPOS if en_cadena[event_id][c] != en_bd[event_id][c]]
        if cambiados:
            problemas.append(
                f"Evento #{event_id}: modificado en tracking_events ({', '.join(cambiados)})."
            )
    for event_id in sorted(en_bd.keys() - en_cadena.keys()):
        problemas.append(
            f"Evento #{event_id}: está en tracking_events pero no se registró al guardarlo "
            "(insertado por fuera de la aplicación)."
        )

    if problemas:
        total = len(problemas)
        return (
            False,
            f"Integridad comprometida: {total} problema(s) entre tracking_events y la cadena local.",
            problemas[:MAX_PROBLEMAS],
        )
    return True, f"Cadena íntegra: {len(en_bd)} eventos verificados contra tracking_events.", []
