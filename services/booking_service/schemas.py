from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


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


class PeerReserveRequest(BaseModel):
    booking_id: str
    segment_id: str
    region: str
    driver_id: str
    slot_start: datetime
    slot_end: datetime


class RoutePreviewRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    departure_time: datetime


class RoutePreviewSegment(BaseModel):
    segment_id: str
    segment_name: str
    region: str
    distance_km: float
    duration_minutes: int
    slot_start: datetime
    slot_end: datetime
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None


class RoutePreviewOut(BaseModel):
    route_available: bool
    reason: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    region_chain: List[str] = Field(default_factory=list)
    segments: List[RoutePreviewSegment] = Field(default_factory=list)