"""
Cadena de custodia.

Cada vez que se completa un análisis (de cualquier módulo), se calcula la
huella SHA-256 de su contenido y se encadena con la huella del eslabón
anterior — igual que un blockchain simplificado:

    chain_hash[N] = SHA256(chain_hash[N-1] + evidence_hash[N])

Esto hace que la cadena sea "a prueba de manipulación selectiva": si
alguien edita a mano un caso antiguo directamente en la base de datos, su
evidence_hash ya no coincide con el guardado, y el chain_hash de ESE
eslabón y de TODOS los posteriores deja de cuadrar al recalcularlos — se
detecta con una simple verificación (`verify_chain`).

Honestidad académica sobre qué garantiza esto y qué NO:
- SÍ detecta manipulación de un caso pasado, tanto si se toca la tabla
  del caso en sí (`cases`, `email_cases`...) como si se toca la propia
  tabla `integrity_ledger` — la verificación recalcula el hash desde los
  datos actuales de cada caso y comprueba también que la cadena de
  eslabones sea consistente consigo misma (ver `verify_chain`).
- NO es un blockchain de verdad: no está distribuido ni descentralizado,
  sigue siendo una única base de datos. Alguien con acceso de
  administrador podría, en teoría, reescribir el caso Y su eslabón del
  libro de registro a la vez de forma coherente, y la verificación no lo
  detectaría (recalcularía el mismo hash "correcto" a partir de los
  datos ya manipulados). Para defenderse de eso haría falta anclar
  periódicamente el `chain_hash` más reciente en algún sitio externo e
  inmutable (ej. publicarlo, o en una blockchain pública de verdad) —
  fuera del alcance de este proyecto, pero es la ampliación natural si
  hiciera falta un nivel de garantía mayor.
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.integrity_ledger import IntegrityLedgerEntry
from app.services import integrity_payloads

GENESIS_HASH = "0" * 64


def _canonical_json(payload: dict) -> str:
    """
    Serialización determinista: mismas claves en el mismo orden siempre,
    para que el mismo contenido dé siempre el mismo hash sin importar en
    qué orden se construyó el diccionario en Python.
    """
    return json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)


def compute_evidence_hash(payload: dict) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def record_evidence(db: Session, case_type: str, case_id: int, payload: dict) -> IntegrityLedgerEntry:
    """Añade un nuevo eslabón a la cadena para esta evidencia. Se llama justo después de persistir cada caso."""
    evidence_hash = compute_evidence_hash(payload)

    last_entry = db.query(IntegrityLedgerEntry).order_by(desc(IntegrityLedgerEntry.id)).first()
    previous_chain_hash = last_entry.chain_hash if last_entry else GENESIS_HASH

    chain_hash = hashlib.sha256(f"{previous_chain_hash}{evidence_hash}".encode("utf-8")).hexdigest()

    entry = IntegrityLedgerEntry(
        case_type=case_type,
        case_id=case_id,
        evidence_hash=evidence_hash,
        previous_chain_hash=previous_chain_hash,
        chain_hash=chain_hash,
        captured_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> tuple[bool, int | None]:
    """
    Verificación en dos capas, en este orden:

    1. Consistencia interna del propio libro de registro: cada
       chain_hash tiene que ser SHA256(chain_hash_anterior + evidence_hash).
       Esto detecta si alguien ha tocado la propia tabla `integrity_ledger`
       (p.ej. reescribir un evidence_hash a mano).
    2. Consistencia contra el caso real: se reconstruye el payload de
       evidencia a partir del caso TAL Y COMO ESTÁ AHORA en su tabla
       (cases, email_cases, wallet_cases...) usando la misma función que
       se usó al capturarlo (integrity_payloads.py), se vuelve a
       hashear, y se compara con el evidence_hash guardado. Esto es lo
       que de verdad detecta que alguien haya editado un caso antiguo
       directamente en la base de datos — sin esta capa, el libro de
       registro podría estar perfectamente encadenado consigo mismo y
       aun así no reflejar el estado real de la evidencia.

    Devuelve (integra: bool, id_del_primer_eslabon_roto_o_None).
    """
    entries = db.query(IntegrityLedgerEntry).order_by(asc(IntegrityLedgerEntry.id)).all()
    previous = GENESIS_HASH

    for entry in entries:
        # Capa 1: consistencia interna de la cadena
        expected_chain_hash = hashlib.sha256(f"{previous}{entry.evidence_hash}".encode("utf-8")).hexdigest()
        if entry.previous_chain_hash != previous or entry.chain_hash != expected_chain_hash:
            return False, entry.id
        previous = entry.chain_hash

        # Capa 2: el caso real sigue coincidiendo con lo que se hasheó al capturarlo
        registry_entry = integrity_payloads.REGISTRY.get(entry.case_type)
        if registry_entry is None:
            continue  # tipo de caso desconocido (no debería pasar) -> no se puede comprobar, se ignora esta capa
        model, build_payload = registry_entry
        case = db.query(model).filter(model.id == entry.case_id).first()
        if case is None:
            return False, entry.id  # el caso ha desaparecido -> la evidencia ya no se puede verificar
        recomputed_hash = compute_evidence_hash(build_payload(case))
        if recomputed_hash != entry.evidence_hash:
            return False, entry.id

    return True, None


def get_entry_for_case(db: Session, case_type: str, case_id: int) -> IntegrityLedgerEntry | None:
    return (
        db.query(IntegrityLedgerEntry)
        .filter(IntegrityLedgerEntry.case_type == case_type, IntegrityLedgerEntry.case_id == case_id)
        .order_by(desc(IntegrityLedgerEntry.id))
        .first()
    )
