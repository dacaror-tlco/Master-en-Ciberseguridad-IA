from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.ip.models import IpCase


def create_case(db: Session, case: IpCase) -> IpCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> IpCase | None:
    return db.query(IpCase).filter(IpCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[IpCase]:
    return db.query(IpCase).order_by(desc(IpCase.created_at)).offset(skip).limit(limit).all()
