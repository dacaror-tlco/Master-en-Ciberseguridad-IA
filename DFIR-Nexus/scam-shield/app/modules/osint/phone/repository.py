from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.phone.models import PhoneCase


def create_case(db: Session, case: PhoneCase) -> PhoneCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> PhoneCase | None:
    return db.query(PhoneCase).filter(PhoneCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[PhoneCase]:
    return db.query(PhoneCase).order_by(desc(PhoneCase.created_at)).offset(skip).limit(limit).all()
