from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.modules.osint.image.models import FacialSearchCase, ImageCase, ReverseImageSearchCase


def create_image_case(db: Session, case: ImageCase) -> ImageCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_image_case(db: Session, case_id: int) -> ImageCase | None:
    return db.query(ImageCase).filter(ImageCase.id == case_id).first()


def list_image_cases(db: Session, skip: int = 0, limit: int = 50) -> list[ImageCase]:
    return db.query(ImageCase).order_by(desc(ImageCase.created_at)).offset(skip).limit(limit).all()


def all_image_cases(db: Session) -> list[ImageCase]:
    return db.query(ImageCase).all()


def create_reverse_search_case(db: Session, case: ReverseImageSearchCase) -> ReverseImageSearchCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def create_facial_search_case(db: Session, case: FacialSearchCase) -> FacialSearchCase:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case
