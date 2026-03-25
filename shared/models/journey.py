from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    SAGA_IN_PROGRESS = "SAGA_IN_PROGRESS"


class RouteSegment(BaseModel):
    segment_id: str
    name: str
    region: str
    time_slot_start: datetime
    time_slot_end: datetime


class BookingRequest(BaseModel):
    driver_id: str
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    departure_time: datetime
    plate_number: Optional[str] = None


class BookingResponse(BaseModel):
    booking_id: str
    status: BookingStatus
    segments: List[RouteSegment] = []
    estimated_duration_minutes: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SegmentReservation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    segment_id: str
    region: str
    time_slot_start: datetime
    time_slot_end: datetime
    status: BookingStatus = BookingStatus.PENDING
