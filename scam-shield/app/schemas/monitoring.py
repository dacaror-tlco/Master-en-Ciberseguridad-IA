from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MonitoredSubjectResponse(BaseModel):
    id: int
    case_type: str
    identifier: str
    enabled: bool
    check_interval_hours: int
    last_case_id: Optional[int] = None
    last_score: Optional[int] = None
    last_bucket: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MonitoredSubjectUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    check_interval_hours: Optional[int] = Field(None, ge=1, le=24 * 30, description="Cada cuántas horas re-chequear este sujeto")


class RiskAlertResponse(BaseModel):
    id: int
    subject_id: int
    case_type: str
    identifier: str
    previous_case_id: Optional[int] = None
    previous_score: Optional[int] = None
    previous_bucket: Optional[str] = None
    new_case_id: int
    new_score: int
    new_bucket: str
    reason: str
    new_flag_codes: list[str] = []
    acknowledged: bool
    detected_at: datetime

    class Config:
        from_attributes = True


class CheckNowResponse(BaseModel):
    subject: MonitoredSubjectResponse
    alert: Optional[RiskAlertResponse] = None
    error: Optional[str] = None
