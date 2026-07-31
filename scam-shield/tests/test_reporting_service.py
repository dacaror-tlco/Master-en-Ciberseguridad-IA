from app.services.reporting_service import recommend_channels


def test_siempre_incluye_policia():
    channels = recommend_channels({"domain"})
    assert any(c.name.startswith("Policía") for c in channels)


def test_wallet_incluye_gdt():
    channels = recommend_channels({"wallet"})
    names = [c.name for c in channels]
    assert any("GDT" in n for n in names)


def test_cnmv_incluye_cnmv():
    channels = recommend_channels({"cnmv"})
    assert any("CNMV" in c.name for c in channels)


def test_sin_duplicados_con_varios_tipos():
    channels = recommend_channels({"domain", "email", "typosquatting"})
    names = [c.name for c in channels]
    assert len(names) == len(set(names))
