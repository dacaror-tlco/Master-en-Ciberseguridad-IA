"""
Cómo extraer el "sujeto" (qué se analizó) de cada tipo de caso, para
normalizarlo en `osint_findings`.

Cada caso guarda su identificador en una columna distinta (`domain`,
`from_address`, `address`, `ip`...). Aquí se mapea case_type -> cómo
sacar (subject_type, subject_value) y qué etiqueta humana usar en el
`headline`. Es el mismo vocabulario de case_type que usa
integrity_ledger / monitoring.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SubjectSpec:
    subject_type: str          # categoría normalizada (domain, email_address, ...)
    label: str                 # etiqueta humana para el headline ("Dominio", "Email", ...)
    extract: Callable[[object], str]   # saca el identificador de la instancia del caso


def _first_attr(case: object, *names: str) -> str:
    for name in names:
        value = getattr(case, name, None)
        if value:
            return str(value)
    return "(desconocido)"


REGISTRY: dict[str, SubjectSpec] = {
    "domain": SubjectSpec("domain", "Dominio", lambda c: _first_attr(c, "domain")),
    "email": SubjectSpec("email_address", "Email", lambda c: _first_attr(c, "from_address")),
    "wallet": SubjectSpec("crypto_wallet", "Wallet", lambda c: _first_attr(c, "address", "wallet")),
    "typosquatting": SubjectSpec("domain", "Dominio (typosquatting)", lambda c: _first_attr(c, "domain")),
    "phone": SubjectSpec("phone_number", "Teléfono", lambda c: _first_attr(c, "phone", "raw_phone")),
    "cnmv": SubjectSpec("entity_name", "Entidad", lambda c: _first_attr(c, "query")),
    "ip": SubjectSpec("ip_address", "IP", lambda c: _first_attr(c, "ip")),
    "image": SubjectSpec("image_file", "Imagen", lambda c: _first_attr(c, "filename", "perceptual_hash")),
    "image_reverse_search": SubjectSpec(
        "image_file", "Búsqueda inversa de imagen", lambda c: _first_attr(c, "source_sha256")
    ),
    "image_facial_search": SubjectSpec(
        "image_file", "Búsqueda facial", lambda c: _first_attr(c, "source_sha256")
    ),
}

_LEVEL_LABEL = {"low": "RIESGO BAJO", "medium": "RIESGO MEDIO", "high": "RIESGO ALTO"}


def build_headline(spec: SubjectSpec, subject_value: str, risk_level: str, risk_score: int) -> str:
    headline = f"{spec.label} {subject_value} — {_LEVEL_LABEL.get(risk_level, risk_level.upper())} ({risk_score})"
    return headline[:255]
