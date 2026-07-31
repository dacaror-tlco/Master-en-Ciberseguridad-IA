"""
Schemas de entrada/salida para el análisis de wallets de criptomonedas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import RiskFlag


class WalletAnalysisRequest(BaseModel):
    address: str = Field(
        ...,
        description="Dirección de wallet BTC, ETH o Tron (TRC20)",
        examples=["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
    )


class ExtractAddressesRequest(BaseModel):
    text: str = Field(..., description="Texto libre (mensaje, email, chat...) del que extraer direcciones cripto")


class ExtractedAddress(BaseModel):
    address: str
    chain: str  # "BTC" | "ETH" | "TRON"


class ExtractAddressesResponse(BaseModel):
    candidates: list[ExtractedAddress] = []


class AddressFormatResponse(BaseModel):
    chain: Optional[str] = None  # "BTC" | "ETH" | "TRON" | None si no se reconoce
    subtype: Optional[str] = None  # p.ej. "bech32 (SegWit nativo)", solo para BTC
    valid: bool = False


class WalletInfo(BaseModel):
    chain: str  # "BTC" | "ETH" | "TRON"
    address: str
    n_transactions: int
    total_received: float  # en la unidad nativa (BTC/ETH), o en `token` si no es None
    total_sent: float
    balance: float  # siempre en la moneda nativa de la red (BTC/ETH/TRX), independientemente de `token`
    first_transaction_at: Optional[datetime] = None
    unique_senders_recent: int = Field(0, description="Direcciones distintas que han enviado fondos, entre las últimas transacciones analizadas")
    note: Optional[str] = None  # p.ej. avisos de limitación de la API pública
    token: Optional[str] = None  # p.ej. "USDT-TRC20": si se rellena, total_received/total_sent están en esa unidad, no en la nativa
    evm_network: Optional[str] = None  # para chain="ETH": qué red EVM se usó realmente (Ethereum/BSC/Polygon)
    ofac_sanctioned: bool = False  # True si la dirección aparece en la lista de sancionados de la OFAC (EEUU)


class WalletAnalysisResponse(BaseModel):
    wallet: WalletInfo
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime


class WalletCaseResponse(WalletAnalysisResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WalletCaseListItem(BaseModel):
    id: int
    chain: str
    address: str
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
