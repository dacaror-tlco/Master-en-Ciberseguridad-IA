from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.typosquatting.models import TyposquattingCase


def create_case(db: Session, case: TyposquattingCase) -> TyposquattingCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> TyposquattingCase | None:
    return db.query(TyposquattingCase).filter(TyposquattingCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[TyposquattingCase]:
    return db.query(TyposquattingCase).order_by(desc(TyposquattingCase.created_at)).offset(skip).limit(limit).all()
