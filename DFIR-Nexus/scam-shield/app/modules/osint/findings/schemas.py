from datetime import datetime

from pydantic import BaseModel


class FindingListItem(BaseModel):
    """Fila de `osint_findings` tal y como la consumen tracking / informes / timeline."""
    id: int
    case_type: str
    source_table: str
    source_id: int
    case_id: int | None = None
    subject_type: str
    subject_value: str
    risk_score: int
    risk_level: str
    headline: str
    flag_count: int
    analyzed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FindingDetail(FindingListItem):
    """Igual que el item de lista, más las señales y el payload completo del caso."""
    top_flags: list = []
    details: dict = {}
