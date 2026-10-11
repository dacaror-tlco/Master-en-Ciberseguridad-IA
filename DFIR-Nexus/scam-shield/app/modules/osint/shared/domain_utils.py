"""Normalización de dominio compartida entre el módulo de dominio y el de typosquatting."""


def normalize_domain(raw: str) -> str:
    return raw.strip().lower().removeprefix("http://").removeprefix("https://").removeprefix("www.").rstrip("/")
