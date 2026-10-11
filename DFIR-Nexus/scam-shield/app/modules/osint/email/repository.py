from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.email.models import EmailCase


def create_case(db: Session, case: EmailCase) -> EmailCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> EmailCase | None:
    return db.query(EmailCase).filter(EmailCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[EmailCase]:
    return db.query(EmailCase).order_by(desc(EmailCase.created_at)).offset(skip).limit(limit).all()
