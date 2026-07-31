from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IntegrityLedgerEntryResponse(BaseModel):
    id: int
    case_type: str
    case_id: int
    evidence_hash: str
    previous_chain_hash: str
    chain_hash: str
    captured_at: datetime

    class Config:
        from_attributes = True


class ChainVerificationResponse(BaseModel):
    intact: bool
    total_entries: int
    broken_at_entry_id: Optional[int] = None
    message: str
