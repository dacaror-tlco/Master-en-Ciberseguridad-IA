from app.services.typosquatting_service import generate_variants


def test_genera_variantes_de_varias_tecnicas():
    variants = generate_variants("bbva.es")
    techniques = {t for _, t in variants}
    assert {"omission", "duplication", "transposition", "tld_swap", "phishing_keyword"} <= techniques


def test_no_incluye_el_dominio_original():
    variants = generate_variants("bbva.es")
    names = [v for v, _ in variants]
    assert "bbva.es" not in names


def test_no_hay_duplicados():
    variants = generate_variants("bbva.es")
    names = [v for v, _ in variants]
    assert len(names) == len(set(names))


def test_respeta_el_limite():
    variants = generate_variants("bbva.es", limit=10)
    assert len(variants) <= 10


def test_tld_swap_mantiene_el_nombre():
    variants = generate_variants("miempresa.com")
    tld_swaps = [v for v, t in variants if t == "tld_swap"]
    assert "miempresa.net" in tld_swaps
    assert "miempresa.xyz" in tld_swaps
    assert "miempresa.com" not in tld_swaps  # el TLD original no se cuenta como "swap"


def test_keyword_combinations_incluyen_palabras_de_phishing():
    variants = generate_variants("miempresa.com")
    keyword_variants = [v for v, t in variants if t == "phishing_keyword"]
    assert "miempresa-verificacion.com" in keyword_variants


def test_dominio_sin_tld_devuelve_lista_vacia():
    assert generate_variants("sindominio") == []


def test_omission_genera_variantes_mas_cortas():
    variants = generate_variants("test.com")
    omissions = [v for v, t in variants if t == "omission"]
    assert "est.com" in omissions
    assert "tst.com" in omissions
