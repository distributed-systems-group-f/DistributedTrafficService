from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VerificationResult(BaseModel):
    plate_number: str
    is_authorized: bool
    booking_id: Optional[str] = None
    status: Optional[str] = None
    message: str
    checked_at: datetime
