"""
Tests del servicio de cadena de custodia. Usan directamente la sesión de
base de datos de la fixture `client` (a través de su motor en memoria),
no hace falta ningún mock — todo es lógica pura de hashing.
"""
from app.services import integrity_service


def test_hash_es_deterministico():
    payload = {"a": 1, "b": "texto"}
    assert integrity_service.compute_evidence_hash(payload) == integrity_service.compute_evidence_hash(payload)


def test_hash_no_depende_del_orden_de_las_claves():
    h1 = integrity_service.compute_evidence_hash({"a": 1, "b": 2})
    h2 = integrity_service.compute_evidence_hash({"b": 2, "a": 1})
    assert h1 == h2


def test_payloads_distintos_dan_hashes_distintos():
    h1 = integrity_service.compute_evidence_hash({"score": 10})
    h2 = integrity_service.compute_evidence_hash({"score": 11})
    assert h1 != h2
