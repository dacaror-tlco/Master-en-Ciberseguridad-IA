from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.cases.models import AccionAuditoria, EstadoCaso


class CaseBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    responsable: str


class CaseCreate(CaseBase):
    estado: EstadoCaso = EstadoCaso.ABIERTO


class CaseUpdate(BaseModel):
    nombre: str | None = None
    estado: EstadoCaso | None = None
    descripcion: str | None = None
    responsable: str | None = None


class CaseRead(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoCaso
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    eliminado: bool
    fecha_eliminacion: datetime | None


class EvidenceBase(BaseModel):
    tipo: str
    valor: str
    observaciones: str | None = None
    fecha_adquisicion: datetime | None = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    """
    Deliberadamente SIN `tipo` ni `valor`: son el contenido probatorio de la
    evidencia y son inmutables una vez creada (ver models.Evidence.hash_valor
    y integrity.py). Solo se puede anotar (`observaciones`) o completar el
    dato de procedencia (`fecha_adquisicion`) si no se conocía al crearla.
    Para corregir un `tipo`/`valor` erróneo, el flujo correcto es eliminar
    (lógicamente) esa evidencia y registrar una nueva — ambas operaciones
    quedan en case_audit_log.
    """

    observaciones: str | None = None
    fecha_adquisicion: datetime | None = None


class EvidenceRead(EvidenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    fecha_subida: datetime
    fecha_actualizacion: datetime
    hash_valor: str
    eliminado: bool
    fecha_eliminacion: datetime | None


class EvidenceIntegrityCheck(BaseModel):
    """Respuesta de GET /cases/{case_id}/evidences/{evidence_id}/integridad."""

    evidence_id: int
    algoritmo: str
    hash_registrado: str
    hash_actual: str
    integro: bool


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    evidence_id: int | None
    accion: AccionAuditoria
    actor: str
    detalle: dict | None
    creado_en: datetime


class OsintVinculacionAudit(BaseModel):
    """
    Body de POST /cases/{case_id}/auditoria/osint. Endpoint estrecho: solo
    permite registrar ESTA acción (osint_vinculacion_cambiada), no una API
    genérica para que cualquier backend escriba cualquier entrada de
    auditoría. Lo llama scam-shield (OSINT) tras persistir con éxito, en su
    propia tabla, el cambio de `case_id` de una investigación — nunca antes.

    `case_anterior`/`case_nuevo` distinguen los tres escenarios (NULL->caso,
    caso->otro caso, caso->NULL); al menos uno de los dos debe coincidir con
    el `case_id` de la URL (el caso al que se adjunta esta entrada de
    auditoría), y ambos no pueden ser nulos a la vez (no habría cambio real
    que auditar).

    Fase 4: deliberadamente SIN `actor` — antes lo fijaba el propio
    llamador (con el valor por defecto "osint", nunca verificado); ahora
    lo resuelve este backend a partir del JWT reenviado por OSINT (ver
    routes.py::registrar_vinculacion_osint y
    auth/dependencies.py::resolve_osint_actor), no de un dato que el
    cliente pudiera fijar libremente en el body.
    """

    case_type: str
    source_id: int
    subject_value: str | None = None
    case_anterior: int | None = None
    case_nuevo: int | None = None
