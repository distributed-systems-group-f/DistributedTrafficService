from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class BookingCreateRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    departure_time: datetime
    plate_number: Optional[str] = None


class ReservationOut(BaseModel):
    segment_id: str
    region: str
    time_slot_start: datetime
    time_slot_end: datetime
    status: str


class BookingOut(BaseModel):
    booking_id: str
    status: str
    segments: List[ReservationOut] = []
    estimated_duration_minutes: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
