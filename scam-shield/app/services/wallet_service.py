"""
Servicio de consulta de wallets de criptomonedas.

Usa APIs públicas de exploradores de blockchain. A diferencia del WHOIS o
el email, esto no depende de ningún permiso ni requiere autenticación para
BTC ni Tron: los ledgers son públicos por diseño. Esa es precisamente la
razón por la que trazar cripto es mucho más fiable como evidencia que, por
ejemplo, capturar una IP: nadie puede "borrar" ni negar una transacción ya
confirmada en la blockchain.

Fuentes:
- BTC: blockchain.info (API pública, sin necesidad de API key)
- ETH y otras redes EVM (BSC, Polygon): Etherscan V2, misma API key para todas
- TRON/TRC20: TronGrid (API pública oficial, sin key obligatoria)
"""
import re
from datetime import datetime, timezone

import requests

from app.core.config import settings
from app.schemas.wallet_analysis import WalletInfo

_ETH_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")
_BTC_PATTERN = re.compile(r"^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$")
_TRON_PATTERN = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")

# Versiones SIN anclar de los mismos formatos, para escanear texto libre
# (mensajes de estafa, emails...) en vez de validar una dirección exacta.
# Cada candidato encontrado así se re-valida con detect_chain() antes de
# devolverlo, para descartar los falsos positivos de un escaneo laxo.
_ETH_SCAN = re.compile(r"0x[a-fA-F0-9]{40}")
_BTC_SCAN = re.compile(r"bc1[a-zA-HJ-NP-Z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}")
_TRON_SCAN = re.compile(r"T[1-9A-HJ-NP-Za-km-z]{33}")

_RECENT_TX_LIMIT = 50  # cuántas transacciones recientes analizamos como muestra

# Etherscan cerró su API V1 en 2025: ahora todo pasa por un único endpoint
# V2 con un parámetro chainid que indica la red. La misma API key gratuita
# vale para las tres — por eso podemos comprobar varias redes EVM sin pedir
# nada nuevo al usuario. El orden importa: es el orden en que se comprueban,
# y se usa la que tenga más transacciones si hay actividad en más de una.
_ETHERSCAN_V2_BASE_URL = "https://api.etherscan.io/v2/api"
_EVM_CHAINS = [("Ethereum", 1), ("BSC", 56), ("Polygon", 137)]

_TRONGRID_BASE_URL = "https://api.trongrid.io"
_USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


def detect_chain(address: str) -> str:
    address = address.strip()
    if _ETH_PATTERN.match(address):
        return "ETH"
    if _BTC_PATTERN.match(address):
        return "BTC"
    if _TRON_PATTERN.match(address):
        return "TRON"
    raise ValueError(f"'{address}' no tiene formato de dirección BTC, ETH ni Tron reconocible")


def _btc_subtype(address: str) -> str:
    if address.startswith("bc1p"):
        return "taproot (bech32m)"
    if address.startswith("bc1"):
        return "bech32 (SegWit nativo)"
    if address.startswith("3"):
        return "P2SH-SegWit"
    return "legacy"


def describe_address_format(address: str) -> dict:
    """
    Para la ayuda de formato en vivo del frontend: a diferencia de
    detect_chain(), nunca lanza excepción — devuelve `chain=None` si el
    formato no se reconoce, para poder dar feedback mientras el usuario
    todavía está escribiendo.
    """
    address = address.strip()
    try:
        chain = detect_chain(address)
    except ValueError:
        return {"chain": None, "subtype": None, "valid": False}

    subtype = _btc_subtype(address) if chain == "BTC" else None
    return {"chain": chain, "subtype": subtype, "valid": True}


def extract_addresses(text: str) -> list[dict]:
    """
    Escanea un bloque de texto libre (p.ej. un mensaje de estafa pegado
    tal cual) y devuelve todas las direcciones cripto reconocibles que
    contiene, con su chain. Pensado para el caso real de "tengo un chat
    entero y no sé encontrar la dirección a mano".
    """
    candidates = set(_ETH_SCAN.findall(text)) | set(_BTC_SCAN.findall(text)) | set(_TRON_SCAN.findall(text))
    results = []
    for candidate in candidates:
        try:
            results.append({"address": candidate, "chain": detect_chain(candidate)})
        except ValueError:
            continue  # falso positivo del escaneo laxo (p.ej. un hash de tx, no una dirección)
    return results


def get_btc_wallet_info(address: str) -> WalletInfo:
    resp = requests.get(
        f"https://blockchain.info/rawaddr/{address}",
        params={"limit": _RECENT_TX_LIMIT},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    txs = data.get("txs", [])
    first_tx_time = None
    if txs:
        oldest = min(txs, key=lambda t: t["time"])
        first_tx_time = datetime.fromtimestamp(oldest["time"], tz=timezone.utc)

    unique_senders = {
        (inp.get("prev_out") or {}).get("addr")
        for tx in txs
        for inp in tx.get("inputs", [])
        if (inp.get("prev_out") or {}).get("addr") not in (None, address)
    }

    n_tx = data.get("n_tx", 0)

    return WalletInfo(
        chain="BTC",
        address=address,
        n_transactions=n_tx,
        total_received=data.get("total_received", 0) / 1e8,
        total_sent=data.get("total_sent", 0) / 1e8,
        balance=data.get("final_balance", 0) / 1e8,
        first_transaction_at=first_tx_time,
        unique_senders_recent=len(unique_senders),
        note=(
            f"Solo se han analizado las últimas {_RECENT_TX_LIMIT} transacciones de {n_tx} totales "
            "(limitación de la API pública); la fecha de 'primera transacción' puede no ser la real."
        ) if n_tx > _RECENT_TX_LIMIT else None,
    )


def _fetch_evm_balance(chain_id: int, address: str) -> int:
    resp = requests.get(
        _ETHERSCAN_V2_BASE_URL,
        params={
            "chainid": chain_id,
            "module": "account", "action": "balance", "address": address,
            "tag": "latest", "apikey": settings.etherscan_api_key,
        },
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json().get("result", "0")
    if not str(result).lstrip("-").isdigit():
        # Etherscan devuelve un mensaje de texto en vez de un número cuando algo
        # va mal (endpoint deprecado, rate limit, red sin soporte, etc.)
        raise RuntimeError(f"Etherscan respondió con un error: {result}")
    return int(result)


def _fetch_evm_txlist(chain_id: int, address: str) -> list[dict]:
    resp = requests.get(
        _ETHERSCAN_V2_BASE_URL,
        params={
            "chainid": chain_id,
            "module": "account", "action": "txlist", "address": address,
            "sort": "asc", "offset": _RECENT_TX_LIMIT, "page": 1,
            "apikey": settings.etherscan_api_key,
        },
        timeout=10,
    )
    resp.raise_for_status()
    txs = resp.json().get("result", [])
    return txs if isinstance(txs, list) else []


def get_eth_wallet_info(address: str) -> WalletInfo:
    if not settings.etherscan_api_key:
        raise RuntimeError(
            "No hay ETHERSCAN_API_KEY configurada. Consigue una gratuita en https://etherscan.io/apis "
            "y añádela a tu archivo .env"
        )

    checked_networks: list[str] = []
    best: dict | None = None  # {"network", "balance_wei", "txs"}
    for network_name, chain_id in _EVM_CHAINS:
        try:
            balance_wei = _fetch_evm_balance(chain_id, address)
            txs = _fetch_evm_txlist(chain_id, address)
        except Exception:
            continue  # esta red concreta falló (rate limit, no soportada...); se prueban las demás
        checked_networks.append(network_name)
        if best is None or len(txs) > len(best["txs"]):
            best = {"network": network_name, "balance_wei": balance_wei, "txs": txs}

    if best is None:
        raise RuntimeError("Etherscan no respondió en ninguna de las redes EVM soportadas (Ethereum/BSC/Polygon)")

    txs = best["txs"]
    first_tx_time = None
    total_received = 0.0
    total_sent = 0.0
    unique_senders = set()

    if txs:
        first_tx_time = datetime.fromtimestamp(int(txs[0]["timeStamp"]), tz=timezone.utc)
        for tx in txs:
            value_eth = int(tx["value"]) / 1e18
            to_addr = (tx.get("to") or "").lower()
            from_addr = (tx.get("from") or "").lower()
            if to_addr == address.lower():
                total_received += value_eth
                if from_addr != address.lower():
                    unique_senders.add(from_addr)
            if from_addr == address.lower():
                total_sent += value_eth

    notes = []
    if len(txs) >= _RECENT_TX_LIMIT:
        notes.append(f"Solo se han analizado las últimas {_RECENT_TX_LIMIT} transacciones (limitación de la API pública).")
    if len(checked_networks) > 1:
        others = [n for n in checked_networks if n != best["network"]]
        notes.append(
            f"Comprobado en {', '.join(checked_networks)} — se ha usado {best['network']} por tener más actividad "
            f"({len(txs)} tx) que {' y '.join(others)}."
        )

    return WalletInfo(
        chain="ETH",
        address=address,
        evm_network=best["network"],
        n_transactions=len(txs),
        total_received=total_received,
        total_sent=total_sent,
        balance=best["balance_wei"] / 1e18,
        first_transaction_at=first_tx_time,
        unique_senders_recent=len(unique_senders),
        note=" ".join(notes) or None,
    )


def get_tron_wallet_info(address: str) -> WalletInfo:
    headers = {"TRON-PRO-API-KEY": settings.tron_api_key} if settings.tron_api_key else {}

    balance_resp = requests.get(f"{_TRONGRID_BASE_URL}/v1/accounts/{address}", headers=headers, timeout=10)
    balance_resp.raise_for_status()
    account_data = balance_resp.json().get("data") or []
    balance_trx = (account_data[0].get("balance", 0) if account_data else 0) / 1e6

    trc20_resp = requests.get(
        f"{_TRONGRID_BASE_URL}/v1/accounts/{address}/transactions/trc20",
        params={"limit": _RECENT_TX_LIMIT, "contract_address": _USDT_TRC20_CONTRACT, "only_confirmed": "true"},
        headers=headers, timeout=10,
    )
    trc20_resp.raise_for_status()
    transfers = trc20_resp.json().get("data", [])

    if transfers:
        # Hay movimientos de USDT-TRC20: es la señal relevante de verdad, porque
        # es la moneda que de verdad piden los estafadores (comisiones bajísimas).
        token = "USDT-TRC20"
        n_tx = len(transfers)
        first_tx_time = datetime.fromtimestamp(int(transfers[-1]["block_timestamp"]) / 1000, tz=timezone.utc)
        total_received = 0.0
        total_sent = 0.0
        unique_senders = set()
        for tr in transfers:
            value = int(tr["value"]) / 1e6  # USDT-TRC20 usa 6 decimales
            to_addr, from_addr = tr.get("to"), tr.get("from")
            if to_addr == address:
                total_received += value
                if from_addr != address:
                    unique_senders.add(from_addr)
            if from_addr == address:
                total_sent += value
        note = (
            f"Solo se han analizado las últimas {_RECENT_TX_LIMIT} transferencias de USDT-TRC20 (limitación de la API pública)."
            if n_tx >= _RECENT_TX_LIMIT else
            "Cifras en USDT-TRC20 (no en TRX nativo): es el token que realmente circula en la mayoría de estafas en esta red."
        )
    else:
        # Sin movimientos de USDT, se recurre al histórico nativo de TRX como respaldo.
        token = None
        native_resp = requests.get(
            f"{_TRONGRID_BASE_URL}/v1/accounts/{address}/transactions",
            params={"limit": _RECENT_TX_LIMIT}, headers=headers, timeout=10,
        )
        native_resp.raise_for_status()
        native_txs = native_resp.json().get("data", [])
        n_tx = len(native_txs)
        first_tx_time = None
        total_received = 0.0
        total_sent = 0.0
        unique_senders: set = set()
        if native_txs:
            first_tx_time = datetime.fromtimestamp(int(native_txs[-1]["block_timestamp"]) / 1000, tz=timezone.utc)
        note = (
            "Sin movimientos de USDT-TRC20; se muestra el histórico nativo de TRX. "
            "Nota: por limitación de la API pública, para TRX nativo no se calculan aquí "
            "los importes recibidos/enviados ni los remitentes distintos (sí para USDT-TRC20)."
        ) if native_txs else None

    return WalletInfo(
        chain="TRON",
        address=address,
        token=token,
        n_transactions=n_tx,
        total_received=total_received,
        total_sent=total_sent,
        balance=balance_trx,
        first_transaction_at=first_tx_time,
        unique_senders_recent=len(unique_senders),
        note=note,
    )


def get_wallet_info(address: str) -> WalletInfo:
    chain = detect_chain(address)
    if chain == "BTC":
        return get_btc_wallet_info(address)
    if chain == "TRON":
        return get_tron_wallet_info(address)
    return get_eth_wallet_info(address)
