from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.domain.models import Case


def create_case(db: Session, *, domain: str, analyzed_at: datetime, risk_score: int, risk_flags: list, errors: list, **extra) -> Case:
    case = Case(domain=domain, analyzed_at=analyzed_at, risk_score=risk_score, risk_flags=risk_flags, errors=errors, **extra)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> Case | None:
    return db.query(Case).filter(Case.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[Case]:
    return db.query(Case).order_by(desc(Case.created_at)).offset(skip).limit(limit).all()
