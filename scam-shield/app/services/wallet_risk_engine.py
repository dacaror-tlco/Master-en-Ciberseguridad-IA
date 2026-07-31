"""
Motor de scoring de riesgo para wallets cripto.

Las señales aquí son distintas a las de dominio/email porque la naturaleza
del dato lo es: en vez de "quién dice ser" (que se puede falsificar), en
blockchain tenemos el histórico real de movimientos, que no se puede
falsificar. Las señales se basan en patrones de comportamiento conocidos
de wallets usadas para estafas:

- Muchas direcciones distintas enviando dinero a la misma wallet en poco
  tiempo ("fan-in") es típico de una wallet de recogida reutilizada para
  varias víctimas de un mismo fraude.
- Los fondos salen casi inmediatamente después de entrar ("rapid outflow")
  es típico de lavado de dinero, para dificultar el rastreo.

Además, si la dirección aparece en la lista de sancionados de la OFAC
(ver ofac_service.py) el score se fuerza a 100 sin importar el resto de
señales: es una prueba documental externa, no una inferencia estadística.
"""
from datetime import datetime, timezone

from app.schemas.domain_analysis import RiskFlag
from app.schemas.wallet_analysis import WalletInfo


def evaluate_wallet_risk(wallet: WalletInfo) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if wallet.n_transactions == 0:
        flags.append(RiskFlag(
            code="WALLET_NO_HISTORY", severity="medium",
            description="La wallet no tiene ninguna transacción registrada (recién creada o nunca usada públicamente)",
        ))
        score += 15

    if wallet.total_received > 0:
        outflow_ratio = wallet.total_sent / wallet.total_received
        if outflow_ratio > 0.9:
            flags.append(RiskFlag(
                code="RAPID_OUTFLOW", severity="high",
                description=f"El {outflow_ratio * 100:.0f}% de los fondos recibidos ya ha salido de la wallet, patrón típico de lavado rápido de fondos",
            ))
            score += 30

    if wallet.unique_senders_recent >= 10:
        flags.append(RiskFlag(
            code="HIGH_FAN_IN", severity="high",
            description=f"{wallet.unique_senders_recent} direcciones distintas han enviado fondos a esta wallet recientemente: patrón típico de una wallet de recogida reutilizada para varias víctimas",
        ))
        score += 35
    elif wallet.unique_senders_recent >= 5:
        flags.append(RiskFlag(
            code="MODERATE_FAN_IN", severity="medium",
            description=f"{wallet.unique_senders_recent} direcciones distintas han enviado fondos a esta wallet recientemente",
        ))
        score += 15

    if wallet.first_transaction_at and wallet.n_transactions > 0:
        age_days = (datetime.now(timezone.utc) - wallet.first_transaction_at).days
        if age_days < 7:
            flags.append(RiskFlag(
                code="WALLET_VERY_NEW", severity="medium",
                description=f"La primera transacción de esta wallet fue hace solo {age_days} días",
            ))
            score += 15

    if wallet.ofac_sanctioned:
        flags.append(RiskFlag(
            code="WALLET_OFAC_SANCTIONED", severity="high",
            description="Esta dirección aparece en la lista de direcciones sancionadas de la OFAC (Tesoro de EEUU) — asociada a delitos graves (ransomware, entidades sancionadas, etc.)",
        ))
        return flags, 100  # señal más dura posible: no se modera con el resto, siempre riesgo máximo

    return flags, min(score, 100)
