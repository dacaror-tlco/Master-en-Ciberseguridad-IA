"""
Vincula/desvincula/cambia el caso de Nexus (Módulo 1, `cases.id`)
asociado a una investigación OSINT.

Reutiliza `integrity_payloads.REGISTRY` (case_type -> modelo SQLAlchemy),
que ya existe para la cadena de integridad, en vez de duplicar la lista de
los 8 tipos en un sitio más — es la misma razón por la que ese registro ya
existía. Todas las investigaciones que gestiona este servicio son las que
ya lista `SavedCasesPage` en el frontend (domain/email/wallet/
typosquatting/phone/cnmv/image/ip); los dos sub-tipos de imagen que
también viven en ese registro (búsqueda inversa, facial) son acciones
sobre un ImageCase, no investigaciones de nivel superior, y se excluyen
aquí a propósito.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.osint.case_link import audit_client
from app.modules.osint.findings.models import OsintFinding
from app.modules.osint.findings.subjects import REGISTRY as SUBJECT_REGISTRY
from app.modules.osint.integrity.payloads import REGISTRY as MODEL_REGISTRY

#: Los 8 tipos que expone /osint/cases (SavedCasesPage) — subconjunto
#: deliberado de MODEL_REGISTRY, ver docstring del módulo.
CASE_TYPES: tuple[str, ...] = (
    "domain", "email", "wallet", "typosquatting", "phone", "cnmv", "image", "ip",
)


class UnknownCaseTypeError(Exception):
    pass


class InvestigationNotFoundError(Exception):
    pass


class TargetCaseNotFoundError(Exception):
    pass


def _subject_value(case_type: str, investigacion: object) -> str | None:
    """Solo para que el detalle de auditoría sea legible (no crítico)."""
    spec = SUBJECT_REGISTRY.get(case_type)
    if spec is None:
        return None
    try:
        return spec.extract(investigacion)[:255]
    except Exception:  # noqa: BLE001 - un fallo aquí no debe impedir el cambio de vinculación
        return None


def _existe_caso_activo(db: Session, case_id: int) -> bool:
    """
    Lectura mínima y directa contra `cases` (tabla que este backend no
    posee) — mismo patrón ya usado por Timeline/Informes para leer tablas
    ajenas (ver docs/CONTRATOS.md): nunca se importa el modelo Python de
    Casos, solo se lee la columna que hace falta. Un caso eliminado
    lógicamente cuenta como "no disponible" para vincular una
    investigación nueva (aunque sí se puede seguir *desvinculando* de él,
    ver routes.py: ese caso no pasa por aquí).
    """
    fila = db.execute(text("SELECT eliminado FROM cases WHERE id = :id"), {"id": case_id}).fetchone()
    return fila is not None and not bool(fila[0])


def actualizar_vinculacion(
    db: Session, case_type: str, investigacion_id: int, nuevo_case_id: int | None
) -> tuple[object, bool, int | None]:
    """
    Devuelve (investigacion, cambiado, case_anterior).

    Si `nuevo_case_id` coincide con el `case_id` actual, no persiste nada
    (ni en la tabla de origen ni en osint_findings) y `cambiado=False` —
    el llamador no debe entonces avisar a la auditoría.

    Si hay cambio real, actualiza en la MISMA transacción (un único
    commit) la tabla de origen de la investigación y, si existe, la fila
    correspondiente en `osint_findings` — para que nunca queden
    inconsistentes entre sí: `osint_findings.case_id` es lo único que leen
    Timeline e Informes, así que si solo se actualizara la tabla de origen
    esos módulos seguirían viendo el vínculo antiguo.
    """
    if case_type not in CASE_TYPES:
        raise UnknownCaseTypeError(case_type)
    modelo = MODEL_REGISTRY[case_type][0]

    investigacion = db.get(modelo, investigacion_id)
    if investigacion is None:
        raise InvestigationNotFoundError(investigacion_id)

    case_anterior = investigacion.case_id
    if case_anterior == nuevo_case_id:
        return investigacion, False, case_anterior

    if nuevo_case_id is not None and not _existe_caso_activo(db, nuevo_case_id):
        raise TargetCaseNotFoundError(nuevo_case_id)

    investigacion.case_id = nuevo_case_id

    finding = (
        db.query(OsintFinding)
        .filter(OsintFinding.case_type == case_type, OsintFinding.source_id == investigacion_id)
        .first()
    )
    if finding is not None:
        finding.case_id = nuevo_case_id

    db.commit()
    db.refresh(investigacion)
    return investigacion, True, case_anterior


def registrar_auditoria(
    *,
    case_type: str,
    investigacion: object,
    case_anterior: int | None,
    case_nuevo: int | None,
    authorization_header: str | None = None,
) -> tuple[bool, str | None]:
    """A qué caso se adjunta la entrada: al nuevo si existe, si no al
    anterior (p. ej. al desvincular, el único caso real involucrado es el
    anterior)."""
    case_id_destino = case_nuevo if case_nuevo is not None else case_anterior
    return audit_client.registrar_cambio_en_auditoria(
        case_id=case_id_destino,
        case_type=case_type,
        source_id=investigacion.id,
        subject_value=_subject_value(case_type, investigacion),
        case_anterior=case_anterior,
        case_nuevo=case_nuevo,
        authorization_header=authorization_header,
    )
