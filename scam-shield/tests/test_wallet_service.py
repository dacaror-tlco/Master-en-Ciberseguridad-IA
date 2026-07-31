import pytest

from app.services.wallet_service import describe_address_format, detect_chain, extract_addresses

BTC_LEGACY = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
BTC_SEGWIT = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
BTC_BECH32 = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
BTC_TAPROOT = "bc1p5cyxnuxmeuwuvkwfem96l6qsqacaddzuxsc9gd6pah4c8u57hpjqzj42gd"
ETH_ADDR = "0x" + "a" * 40
TRON_ADDR = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # contrato oficial de USDT-TRC20, formato válido de dirección Tron


@pytest.mark.parametrize("address,expected", [
    (BTC_LEGACY, "BTC"), (BTC_SEGWIT, "BTC"), (BTC_BECH32, "BTC"),
    (ETH_ADDR, "ETH"), (TRON_ADDR, "TRON"),
])
def test_detect_chain_reconoce_cada_formato(address, expected):
    assert detect_chain(address) == expected


def test_detect_chain_rechaza_formato_no_reconocible():
    with pytest.raises(ValueError):
        detect_chain("esto-no-es-una-wallet")


@pytest.mark.parametrize("address,expected_subtype", [
    (BTC_LEGACY, "legacy"),
    (BTC_SEGWIT, "P2SH-SegWit"),
    (BTC_BECH32, "bech32 (SegWit nativo)"),
    (BTC_TAPROOT, "taproot (bech32m)"),
])
def test_describe_address_format_distingue_subtipos_btc(address, expected_subtype):
    result = describe_address_format(address)
    assert result == {"chain": "BTC", "subtype": expected_subtype, "valid": True}


def test_describe_address_format_eth_sin_subtipo():
    assert describe_address_format(ETH_ADDR) == {"chain": "ETH", "subtype": None, "valid": True}


def test_describe_address_format_no_reconocido_no_lanza_excepcion():
    assert describe_address_format("texto cualquiera") == {"chain": None, "subtype": None, "valid": False}


def test_extract_addresses_encuentra_varias_en_texto_libre():
    text = f"""
    Hola, para el reembolso envía el dinero a esta wallet de bitcoin: {BTC_LEGACY}
    o si prefieres USDT en Tron: {TRON_ADDR}
    Gracias, un saludo (por favor no compartas esto con nadie).
    """
    found = extract_addresses(text)
    assert {(c["address"], c["chain"]) for c in found} == {(BTC_LEGACY, "BTC"), (TRON_ADDR, "TRON")}


def test_extract_addresses_ignora_texto_sin_direcciones():
    assert extract_addresses("este mensaje no contiene ninguna wallet, solo texto normal.") == []


def test_extract_addresses_no_duplica_la_misma_direccion():
    text = f"Manda a {BTC_LEGACY} o si no también vale {BTC_LEGACY} otra vez."
    found = extract_addresses(text)
    assert len(found) == 1
