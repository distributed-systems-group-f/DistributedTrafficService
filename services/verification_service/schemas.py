from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class VerificationResult(BaseModel):
    plate_number: str
    is_authorized: bool
    booking_id: Optional[str] = None
    driver_id: Optional[str] = None
    status: Optional[str] = None
    departure_time: Optional[datetime] = None
    journey_window_end: Optional[datetime] = None
    segments: List[str] = Field(default_factory=list, description="Region names this journey passes through")
    message: str
    # Observability: lets ops know whether Redis or DB served the response
    source: Literal["cache", "database", "not_found"] = "not_found"
    checked_at: datetime


class BatchVerificationRequest(BaseModel):
    plate_numbers: List[str] = Field(..., min_length=1, max_length=50)


class BatchVerificationResponse(BaseModel):
    results: List[VerificationResult]
    total: int = 0
    authorized_count: int = 0

    def model_post_init(self, __context):
        self.total = len(self.results)
        self.authorized_count = sum(1 for r in self.results if r.is_authorized)


class CacheStatsResponse(BaseModel):
    active_booking_keys: int
    total_redis_keys: int
    checked_at: datetime