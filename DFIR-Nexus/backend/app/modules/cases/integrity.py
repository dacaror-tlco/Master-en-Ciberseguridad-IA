"""
Huella de integridad del contenido probatorio de una Evidence.

Deliberadamente mínimo: un único hash SHA-256 sobre `valor` (el dato
probatorio en sí), calculado una vez al crear la evidencia. No es un hash
de fila de base de datos (eso cambiaría con cualquier columna administrativa,
p. ej. fecha_actualizacion, sin que el contenido probatorio se haya tocado) y
no es una cadena de custodia con múltiples eslabones — ver CaseAuditLog para
el "qué pasó, cuándo, quién" y chain_integrity.py de Tracking para el patrón
de hash-chain, que aquí no se replica porque no aporta nada por encima de un
hash simple sobre un único campo inmutable.
"""

import hashlib

ALGORITMO = "sha256"


def calcular_hash_valor(valor: str) -> str:
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()
