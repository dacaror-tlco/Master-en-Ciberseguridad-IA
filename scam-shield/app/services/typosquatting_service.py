"""
Generación de variantes typosquatting a partir de un dominio legítimo.

Implementa las técnicas más comunes que usan los atacantes para registrar
dominios que se parecen a una marca real, con el objetivo de que la
víctima no note la diferencia a simple vista (o que ni siquiera la vea,
en el caso de errores de tecleo).

Deliberadamente NO cubrimos homógrafos Unicode completos (ej. usar una
'а' cirílica en vez de una 'a' latina) en esta primera versión — es una
técnica real pero mucho más rara en campañas contra usuarios
hispanohablantes que las técnicas ASCII de abajo, y añadir soporte IDN
completo es una ampliación futura clara si hace falta.
"""
import re

# Mapa de teclado QWERTY español, para sustituciones "dedo torpe" realistas
_ADJACENT_KEYS = {
    "q": "wa", "w": "qes", "e": "wrd", "r": "etf", "t": "ryg", "y": "tuh",
    "u": "yij", "i": "uok", "o": "ipl", "p": "ol",
    "a": "qsz", "s": "awedz", "d": "serfc", "f": "drtgv", "g": "ftyhb",
    "h": "gyujn", "j": "huikm", "k": "jiol", "l": "kop",
    "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb", "b": "vghn",
    "n": "bhjm", "m": "njk",
}

# Sustituciones visuales típicas (glifos que se confunden a simple vista)
_HOMOGLYPHS = {
    "o": "0", "0": "o", "l": "1", "1": "l", "i": "1",
    "s": "5", "e": "3", "a": "4", "rn": "m", "vv": "w", "g": "q",
}

_COMMON_TLDS = ["com", "net", "org", "info", "xyz", "top", "online", "site", "club", "es", "eu", "app"]

_PHISHING_KEYWORDS = ["verificacion", "secure", "login", "soporte", "seguridad", "actualizacion", "account", "cliente"]

_MAX_EDIT_VARIANTS_PER_TECHNIQUE = 40  # límite por técnica, para no explosionar con dominios largos


def _split_domain(domain: str) -> tuple[str, str]:
    """Separa 'bbva.es' en ('bbva', 'es'). Simplificación: asume TLD de un solo nivel."""
    parts = domain.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return domain, ""


def _omissions(name: str) -> list[str]:
    return [name[:i] + name[i + 1:] for i in range(len(name))][:_MAX_EDIT_VARIANTS_PER_TECHNIQUE]


def _duplications(name: str) -> list[str]:
    return [name[:i] + name[i] + name[i:] for i in range(len(name))][:_MAX_EDIT_VARIANTS_PER_TECHNIQUE]


def _transpositions(name: str) -> list[str]:
    return [
        name[:i] + name[i + 1] + name[i] + name[i + 2:]
        for i in range(len(name) - 1)
    ][:_MAX_EDIT_VARIANTS_PER_TECHNIQUE]


def _adjacent_key_substitutions(name: str) -> list[str]:
    variants = []
    for i, ch in enumerate(name):
        for replacement in _ADJACENT_KEYS.get(ch, ""):
            variants.append(name[:i] + replacement + name[i + 1:])
    return variants[:_MAX_EDIT_VARIANTS_PER_TECHNIQUE]


def _homoglyph_substitutions(name: str) -> list[str]:
    variants = []
    for original, replacement in _HOMOGLYPHS.items():
        if original in name:
            variants.append(name.replace(original, replacement, 1))
    return variants


def _hyphenations(name: str) -> list[str]:
    return [name[:i] + "-" + name[i:] for i in range(1, len(name))][:_MAX_EDIT_VARIANTS_PER_TECHNIQUE]


def _tld_swaps(name: str, original_tld: str) -> list[tuple[str, str]]:
    return [(f"{name}.{tld}", "tld_swap") for tld in _COMMON_TLDS if tld != original_tld]


def _keyword_combinations(name: str, tld: str) -> list[tuple[str, str]]:
    variants = []
    for kw in _PHISHING_KEYWORDS:
        variants.append((f"{name}-{kw}.{tld}", "phishing_keyword"))
        variants.append((f"{kw}-{name}.{tld}", "phishing_keyword"))
    return variants


def generate_variants(domain: str, limit: int = 200) -> list[tuple[str, str]]:
    """
    Devuelve una lista de (variante, técnica), sin duplicados y sin
    incluir el dominio original, recortada a `limit` elementos.
    """
    domain = domain.strip().lower()
    name, tld = _split_domain(domain)
    if not tld:
        return []

    edit_techniques = {
        "omission": _omissions(name),
        "duplication": _duplications(name),
        "transposition": _transpositions(name),
        "adjacent_key": _adjacent_key_substitutions(name),
        "homoglyph": _homoglyph_substitutions(name),
        "hyphenation": _hyphenations(name),
    }

    candidates: list[tuple[str, str]] = []
    seen: set[str] = {domain}

    for technique, names in edit_techniques.items():
        for n in names:
            variant = f"{n}.{tld}"
            if variant not in seen and re.match(r"^[a-z0-9-]+\.[a-z]+$", variant):
                seen.add(variant)
                candidates.append((variant, technique))

    for variant, technique in _tld_swaps(name, tld):
        if variant not in seen:
            seen.add(variant)
            candidates.append((variant, technique))

    for variant, technique in _keyword_combinations(name, tld):
        if variant not in seen:
            seen.add(variant)
            candidates.append((variant, technique))

    return candidates[:limit]
