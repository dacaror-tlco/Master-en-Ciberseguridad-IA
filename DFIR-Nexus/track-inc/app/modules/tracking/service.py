"""
Lógica de negocio del Módulo 3. Orquesta:

  1. Parseo del log (log_parser.py)
  2. Clasificación (motor interno: agent.classifier.engine)
  3. Persistencia oficial en tracking_events (repository.py) — esto es
     lo único que el resto del equipo necesita.
  4. Alimentación de la cadena de hashes interna (chain_integrity.py)
     — capa opcional, invisible fuera de este módulo.
"""

from __future__ import annotations

import threading
from pathlib import Path

from sqlalchemy.orm import Session

from agent.classifier.engine import ClassifierEngine

from . import repository
from .chain_integrity import (
    eventos_guardados_del_log,
    metadatos_por_evento,
    registro_atomico,
    verify_case_chain,
)
from .indicators import extraer_indicadores
from .log_parser import parse_log_text
from .powershell import decodificar_encoded_command
from .schemas import (
    AnalyzeLogResponse,
    AnalyzePreviewItem,
    IndicadorAgregado,
    IndicadorOut,
    SaveEventsRequest,
    SaveEventsResponse,
    TrackingEventOut,
    VerifyIntegrityResponse,
)
from .severity_mapping import criticality_to_severidad, severidad_to_criticality
from .tiempo import a_utc_sin_zona, parsear_zona

RULES_PATH = Path(__file__).parent.parent.parent.parent / "agent" / "classifier" / "rules.yaml"


class CaseNotFoundError(Exception):
    """El case_id indicado no existe. La capa de rutas la traduce a 404."""


class LogYaGuardadoError(Exception):
    """El mismo fichero de log ya se guardó en el caso. La ruta lo traduce a 409."""


class CasoNoModificableError(Exception):
    """El caso existe pero no admite nuevos eventos (eliminado o archivado).
    La ruta lo traduce a 409, con el mismo criterio y mensaje que Casos."""


def exigir_caso_existente(db: Session, case_id: int) -> repository.EstadoCaso:
    """Para CONSULTAR (listar eventos, verificar integridad). Un caso
    eliminado se puede seguir consultando, igual que en Casos: la trazabilidad
    no desaparece con el borrado lógico."""
    estado = repository.estado_caso(db, case_id)
    if not estado.existe:
        raise CaseNotFoundError(f"No existe ningún caso con id={case_id}")
    return estado


def exigir_caso_modificable(db: Session, case_id: int) -> None:
    """Para ESCRIBIR (analizar para guardar, guardar). Mismo criterio que
    Casos (`get_active_case` y los casos archivados): un caso eliminado o
    archivado no admite cambios. Antes Tracking seguía aceptando eventos en
    un caso ya borrado desde Casos."""
    estado = exigir_caso_existente(db, case_id)
    if estado.eliminado:
        raise CasoNoModificableError("El caso está eliminado")
    if estado.estado == "archivado":
        raise CasoNoModificableError("El caso está archivado: es un registro histórico inmutable")


def list_case_options(db: Session) -> list[dict]:
    return repository.list_case_options(db)


_cache_clasificador: tuple[tuple[int, int], ClassifierEngine] | None = None
_cache_lock = threading.Lock()


def _get_classifier() -> ClassifierEngine:
    """Motor con las reglas de rules.yaml, recargado solo si el fichero cambia.

    Antes se releía y validaba el YAML en cada análisis (~40 ms). Se sigue
    cumpliendo lo importante: editar rules.yaml aplica sin reiniciar, porque
    la caché se invalida con la fecha de modificación y el tamaño.
    """
    global _cache_clasificador
    info = RULES_PATH.stat()
    firma = (info.st_mtime_ns, info.st_size)
    with _cache_lock:
        if _cache_clasificador is None or _cache_clasificador[0] != firma:
            _cache_clasificador = (firma, ClassifierEngine.from_yaml(RULES_PATH))
        return _cache_clasificador[1]


def analyze_log_content(text: str, fuente_log: str, zona_horaria: str | None = None) -> AnalyzeLogResponse:
    """
    Parsea y clasifica un log SIN persistir nada — es la vista previa
    que el frontend muestra antes de que el analista confirme el guardado.

    `zona_horaria` es la del equipo que escribió el log (`UTC`, `+02:00`...).
    Lanza ValueError si no es válida.
    """
    zona = parsear_zona(zona_horaria)
    classifier = _get_classifier()
    raw_events = parse_log_text(text, fuente_log=fuente_log, zona=zona)

    preview: list[AnalyzePreviewItem] = []
    counts: dict[str, int] = {}

    for raw_event in raw_events:
        clasificacion = classifier.classify_detallado(raw_event)
        # Lo que esconde un -EncodedCommand también se clasifica: la descarga
        # o la cuenta creada dentro del base64 son las reglas que importan.
        decodificado = decodificar_encoded_command(raw_event.payload["command"])
        if decodificado:
            oculto = raw_event.model_copy(update={"payload": {**raw_event.payload, "command": decodificado}})
            clasificacion = classifier.combinar(clasificacion, classifier.classify_detallado(oculto))
        principal = clasificacion.regla
        severidad = criticality_to_severidad(clasificacion.criticality)
        preview.append(AnalyzePreviewItem(
            hora=raw_event.timestamp,
            evento=raw_event.payload["command"],
            severidad=severidad,
            usuario_detectado=raw_event.payload.get("user"),
            regla=principal.name if principal else None,
            reglas=[r.name for r in clasificacion.reglas],
            mitre=list(dict.fromkeys(t for r in clasificacion.reglas for t in r.mitre)),
            linea_original=raw_event.payload.get("raw_line"),
            numero_linea=raw_event.payload.get("line_number"),
            hora_inferida=bool(raw_event.payload.get("timestamp_inferred")),
            salida=raw_event.payload.get("output"),
            comando_decodificado=decodificado,
            indicadores=[
                IndicadorOut(tipo=i.tipo, valor=i.valor, origen=i.origen)
                for i in extraer_indicadores(
                    raw_event.payload["command"], raw_event.payload.get("output"), decodificado
                )
            ],
            regla_descripcion=principal.descripcion if principal else None,
        ))
        counts[severidad.value] = counts.get(severidad.value, 0) + 1

    return AnalyzeLogResponse(
        total_eventos=len(preview),
        por_severidad=counts,
        eventos=preview,
        indicadores=_agrupar_indicadores(preview),
    )


# Orden de severidad para saber cual es la "maxima" de un indicador que
# aparece en varios eventos.
_PESO_SEVERIDAD = {"baja": 0, "media": 1, "alta": 2, "critica": 3}


def _agrupar_indicadores(eventos: list[AnalyzePreviewItem]) -> list[IndicadorAgregado]:
    """Agrupa por (tipo, valor) y ordena por lo que el perito miraria antes.

    Un indicador que aparece en un comando critico y en seis lineas distintas
    es mas relevante que uno visto una vez en un evento de severidad baja.
    """
    acumulado: dict[tuple[str, str], dict] = {}
    for ev in eventos:
        for ind in ev.indicadores:
            clave = (ind.tipo, ind.valor)
            entrada = acumulado.setdefault(
                clave, {"veces": 0, "lineas": [], "peor": ev.severidad}
            )
            entrada["veces"] += 1
            if ev.numero_linea is not None:
                entrada["lineas"].append(ev.numero_linea)
            if _PESO_SEVERIDAD[ev.severidad.value] > _PESO_SEVERIDAD[entrada["peor"].value]:
                entrada["peor"] = ev.severidad

    agregados = [
        IndicadorAgregado(
            tipo=tipo,
            valor=valor,
            veces=datos["veces"],
            lineas=sorted(datos["lineas"]),
            severidad_maxima=datos["peor"],
        )
        for (tipo, valor), datos in acumulado.items()
    ]
    agregados.sort(
        key=lambda a: (-_PESO_SEVERIDAD[a.severidad_maxima.value], -a.veces, a.tipo, a.valor)
    )
    return agregados


def save_events(db: Session, request: SaveEventsRequest) -> SaveEventsResponse:
    """
    Persiste en tracking_events (MySQL, esquema oficial) y, además,
    alimenta la cadena de hashes local del caso con el mismo contenido
    exacto que se guardó — para que la integridad verificada corresponda
    a lo que de verdad quedó en la base de datos oficial.
    """
    exigir_caso_modificable(db, request.case_id)

    # Base de datos y cadena de integridad se confirman juntas: si una falla,
    # la otra no se queda a medias (ver chain_integrity.registro_atomico). La
    # cadena se abre en exclusiva, así que dos guardados del mismo caso a la
    # vez se ponen en fila en vez de pisarse.
    try:
        with registro_atomico(request.case_id, request.sha256_log) as registrar:
            # Dentro del bloqueo: dos guardados simultáneos del mismo log no
            # pueden pasar ambos la comprobación.
            if request.sha256_log and not request.forzar:
                previos = eventos_guardados_del_log(request.case_id, request.sha256_log)
                if previos:
                    raise LogYaGuardadoError(
                        f"Este fichero de log ya se guardó en el caso ({previos} eventos). "
                        "Guardarlo otra vez duplicaría los eventos; repite con 'forzar' si es intencionado."
                    )
            saved_rows = repository.create_tracking_events(db, [
                {
                    "case_id": request.case_id,
                    "hora": a_utc_sin_zona(item.hora),
                    "evento": item.evento,
                    "severidad": item.severidad,
                    "fuente_log": request.fuente_log,
                    "usuario_detectado": item.usuario_detectado,
                }
                for item in request.eventos
            ])
            # La respuesta se construye ahora, con los ids ya asignados: tras
            # el commit, leer cada fila forzaría una consulta por evento.
            respuesta = SaveEventsResponse(
                guardados=len(saved_rows),
                tracking_events=[
                    _evento_out(row, {"regla": item.regla, "hora_inferida": item.hora_inferida})
                    for row, item in zip(saved_rows, request.eventos)
                ],
            )
            registrar([
                (row, severidad_to_criticality(item.severidad), item.regla, item.hora_inferida)
                for row, item in zip(saved_rows, request.eventos)
            ])
            db.commit()
    except BaseException:
        db.rollback()
        raise

    return respuesta


def get_events_for_case(
    db: Session, case_id: int, skip: int = 0, limit: int | None = None
) -> list[TrackingEventOut]:
    exigir_caso_existente(db, case_id)
    rows = repository.list_by_case(db, case_id, skip, limit)
    metadatos = metadatos_por_evento(case_id)
    return [_evento_out(r, metadatos.get(r.id)) for r in rows]


def _evento_out(row, metadatos: dict | None) -> TrackingEventOut:
    """Fila de tracking_events + la procedencia que guarda la cadena local
    (regla y hora inferida). Sin cadena para esa fila, ambos quedan a None:
    el dato no existe, no es que no hubiera regla."""
    evento = TrackingEventOut.model_validate(row)
    if metadatos:
        evento.regla = metadatos["regla"]
        evento.hora_inferida = metadatos["hora_inferida"]
    return evento


def verify_integrity(db: Session, case_id: int) -> VerifyIntegrityResponse:
    exigir_caso_existente(db, case_id)
    ok, message, problemas = verify_case_chain(case_id, repository.list_by_case(db, case_id))
    return VerifyIntegrityResponse(ok=ok, mensaje=message, problemas=problemas)
