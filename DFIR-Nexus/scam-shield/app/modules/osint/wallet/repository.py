from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.wallet.models import WalletCase


def create_case(db: Session, case: WalletCase) -> WalletCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> WalletCase | None:
    return db.query(WalletCase).filter(WalletCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[WalletCase]:
    return db.query(WalletCase).order_by(desc(WalletCase.created_at)).offset(skip).limit(limit).all()
