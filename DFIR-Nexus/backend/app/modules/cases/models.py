import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoCaso(str, enum.Enum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


class AccionAuditoria(str, enum.Enum):
    """Operaciones sobre Case/Evidence que dejan rastro en case_audit_log."""

    CASE_CREADO = "case_creado"
    CASE_ACTUALIZADO = "case_actualizado"
    CASE_ESTADO_CAMBIADO = "case_estado_cambiado"
    CASE_ELIMINADO = "case_eliminado"
    EVIDENCE_CREADA = "evidence_creada"
    EVIDENCE_ACTUALIZADA = "evidence_actualizada"
    EVIDENCE_ELIMINADA = "evidence_eliminada"
    # Registrada por OSINT (scam-shield), vía POST /cases/{id}/auditoria/osint
    # — el único caso en que una acción de este log la origina otro backend,
    # no este mismo servicio. Cubre los tres escenarios (NULL->caso,
    # caso->otro caso, caso->NULL) con un único valor: el detalle (de/a)
    # distingue cuál fue.
    OSINT_VINCULACION_CAMBIADA = "osint_vinculacion_cambiada"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    estado: Mapped[EstadoCaso] = mapped_column(
        Enum(EstadoCaso, native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=EstadoCaso.ABIERTO,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # updated_at administrativo: se toca en cada UPDATE de fila, no representa
    # ningún evento forense. No confundir con fecha_creacion (alta del
    # registro) ni con los timestamps propios de Evidence (ver ese modelo).
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable: Mapped[str] = mapped_column(String(100), nullable=False)

    # Borrado lógico: un caso forense no se destruye físicamente (ver
    # service.delete_case). `eliminado` es el único campo que determina si
    # un caso está "activo"; `estado` sigue siendo puramente el ciclo de
    # vida de la investigación (abierto/en_progreso/cerrado/archivado),
    # nunca se sobrecarga con un quinto valor "eliminado".
    eliminado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    fecha_eliminacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    evidences: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="case", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Timestamps: tres conceptos distintos, nunca intercambiables ---
    # fecha_subida: cuándo se dio de alta el REGISTRO en el sistema (admin).
    fecha_subida: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # fecha_adquisicion: cuándo ocurrió/se adquirió el hecho forense que la
    # evidencia representa. Puede ser anterior a fecha_subida (se registra
    # más tarde de cuando se obtuvo) y puede no conocerse (nullable).
    fecha_adquisicion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # fecha_actualizacion: cuándo se modificó por última vez el REGISTRO
    # (admin) — p. ej. al editar observaciones. No es un timestamp forense.
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Huella de integridad del CONTENIDO probatorio (valor), calculada una
    # única vez en el momento de creación y nunca recalculada (ver
    # integrity.py). Es deliberadamente distinta de cualquier hash de fila
    # de base de datos: representa la evidencia, no el registro que la
    # almacena. Por eso mismo `valor`/`tipo` son inmutables tras crear la
    # evidencia (ver schemas.EvidenceUpdate) — si se pudieran editar y el
    # hash se recalculara en cada cambio, el hash dejaría de servir para
    # detectar una modificación.
    hash_valor: Mapped[str] = mapped_column(String(64), nullable=False)

    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Borrado lógico, igual que en Case: nunca se destruye físicamente una
    # evidencia. Ver service.delete_evidence.
    eliminado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    fecha_eliminacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="evidences")


class CaseAuditLog(Base):
    """
    Rastro de auditoría único para Case y Evidence (no dos tablas
    paralelas): toda fila referencia siempre un case_id, y evidence_id solo
    cuando la operación fue sobre una evidencia concreta. Cadena de
    custodia de Cases/Evidence en este backend: no sustituye ni duplica la
    cadena de integridad de Tracking (chain_integrity.py, hash-chain de
    eventos de log) ni el integrity_ledger de OSINT — son dominios de datos
    distintos, cada uno auditado donde vive.
    """

    __tablename__ = "case_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True, index=True
    )
    accion: Mapped[AccionAuditoria] = mapped_column(
        Enum(AccionAuditoria, native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Sin sistema de autenticación en el proyecto (fuera de alcance, ver
    # CLAUDE.md), "actor" es hoy un identificador de mejor esfuerzo, no una
    # identidad verificada criptográficamente. Se deja preparado para que,
    # el día que exista auth, baste con pasar el usuario real sin tocar el
    # esquema.
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="api")
    detalle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
