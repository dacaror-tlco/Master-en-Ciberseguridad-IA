from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.cnmv.models import CnmvCheckCase, CnmvWarning


def create_case(db: Session, case: CnmvCheckCase) -> CnmvCheckCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> CnmvCheckCase | None:
    return db.query(CnmvCheckCase).filter(CnmvCheckCase.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 50) -> list[CnmvCheckCase]:
    return db.query(CnmvCheckCase).order_by(desc(CnmvCheckCase.created_at)).offset(skip).limit(limit).all()


def list_warnings(db: Session) -> list[CnmvWarning]:
    return db.query(CnmvWarning).all()


def count_warnings(db: Session) -> int:
    return db.query(CnmvWarning).count()


def newest_warning(db: Session) -> CnmvWarning | None:
    return db.query(CnmvWarning).order_by(desc(CnmvWarning.scraped_at)).first()
