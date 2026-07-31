from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.wallet_case import WalletCase
from app.schemas.wallet_analysis import (
    AddressFormatResponse,
    ExtractAddressesRequest,
    ExtractAddressesResponse,
    WalletAnalysisRequest,
    WalletCaseListItem,
    WalletCaseResponse,
)
from app.services import wallet_service
from app.services.wallet_analysis_service import run_wallet_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/wallet-cases", tags=["wallet-cases"])


@router.post("/wallet", response_model=WalletCaseResponse)
def analyze_wallet(payload: WalletAnalysisRequest, db: Session = Depends(get_db)) -> WalletCase:
    try:
        return run_wallet_analysis(db, payload.address)
    except ValueError as exc:
        # dirección con formato no reconocido -> error del cliente, no del servidor
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar la blockchain: {exc}")


@router.post("/wallet/extract-addresses", response_model=ExtractAddressesResponse)
def extract_wallet_addresses(payload: ExtractAddressesRequest) -> ExtractAddressesResponse:
    return ExtractAddressesResponse(candidates=wallet_service.extract_addresses(payload.text))


@router.get("/wallet/format", response_model=AddressFormatResponse)
def wallet_address_format(address: str) -> AddressFormatResponse:
    return AddressFormatResponse(**wallet_service.describe_address_format(address))


@cases_router.get("", response_model=list[WalletCaseListItem])
def list_wallet_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(WalletCase)
        .order_by(desc(WalletCase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{case_id}", response_model=WalletCaseResponse)
def get_wallet_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(WalletCase).filter(WalletCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de wallet {case_id}")
    return case
