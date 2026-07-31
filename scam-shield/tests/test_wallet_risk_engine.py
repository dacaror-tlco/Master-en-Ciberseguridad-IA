from datetime import datetime, timedelta, timezone

from app.schemas.wallet_analysis import WalletInfo
from app.services.wallet_risk_engine import evaluate_wallet_risk


def _wallet(**overrides) -> WalletInfo:
    base = dict(
        chain="BTC", address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        n_transactions=3, total_received=1.0, total_sent=0.0, balance=1.0,
        first_transaction_at=datetime.now(timezone.utc) - timedelta(days=1000),
        unique_senders_recent=1,
    )
    base.update(overrides)
    return WalletInfo(**base)


def test_wallet_limpia_da_score_bajo():
    flags, score = evaluate_wallet_risk(_wallet())
    assert score < 30


def test_wallet_sin_historial_dispara_no_history():
    flags, _ = evaluate_wallet_risk(_wallet(n_transactions=0, total_received=0, first_transaction_at=None))
    assert "WALLET_NO_HISTORY" in [f.code for f in flags]


def test_salida_rapida_de_fondos_dispara_rapid_outflow():
    flags, score = evaluate_wallet_risk(_wallet(total_received=5.0, total_sent=4.8, balance=0.2))
    assert "RAPID_OUTFLOW" in [f.code for f in flags]
    assert score >= 30


def test_muchos_remitentes_dispara_high_fan_in():
    flags, score = evaluate_wallet_risk(_wallet(unique_senders_recent=12))
    assert "HIGH_FAN_IN" in [f.code for f in flags]
    assert score >= 35


def test_pocos_remitentes_extra_dispara_moderate_fan_in():
    flags, _ = evaluate_wallet_risk(_wallet(unique_senders_recent=6))
    assert "MODERATE_FAN_IN" in [f.code for f in flags]


def test_wallet_muy_nueva_dispara_wallet_very_new():
    flags, _ = evaluate_wallet_risk(_wallet(first_transaction_at=datetime.now(timezone.utc) - timedelta(days=2)))
    assert "WALLET_VERY_NEW" in [f.code for f in flags]


def test_caso_de_estafa_realista_combina_senales():
    wallet = _wallet(
        n_transactions=12, total_received=5.0, total_sent=4.8, balance=0.2,
        unique_senders_recent=12, first_transaction_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    flags, score = evaluate_wallet_risk(wallet)
    codes = {f.code for f in flags}
    assert {"RAPID_OUTFLOW", "HIGH_FAN_IN", "WALLET_VERY_NEW"} <= codes
    assert score == 80  # 30 (rapid outflow) + 35 (high fan-in) + 15 (very new) = 80


def test_direccion_sancionada_por_ofac_fuerza_score_maximo():
    """Regresión: una coincidencia OFAC es una prueba documental externa —
    debe imponerse sobre cualquier combinación de señales de comportamiento."""
    wallet = _wallet(ofac_sanctioned=True)  # por lo demás, wallet "limpia"
    flags, score = evaluate_wallet_risk(wallet)
    assert "WALLET_OFAC_SANCTIONED" in [f.code for f in flags]
    assert score == 100
