from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.osint.wallet import service, wallet_service
from app.modules.osint.wallet.models import WalletCase
from app.modules.osint.wallet.schemas import (
    AddressFormatResponse,
    ExtractAddressesRequest,
    ExtractAddressesResponse,
    WalletAnalysisRequest,
    WalletCaseListItem,
    WalletCaseResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
cases_router = APIRouter(prefix="/wallet-cases", tags=["wallet-cases"])


@router.post("/wallet", response_model=WalletCaseResponse)
def analyze_wallet(payload: WalletAnalysisRequest, db: Session = Depends(get_db)) -> WalletCase:
    try:
        return service.run_wallet_analysis(db, payload.address, case_id=payload.case_id)
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
    return service.list_cases(db, skip, limit)


@cases_router.get("/{case_id}", response_model=WalletCaseResponse)
def get_wallet_case(case_id: int, db: Session = Depends(get_db)):
    case = service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"No existe el caso de wallet {case_id}")
    return case
