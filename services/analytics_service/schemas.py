from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime


class DashboardStats(BaseModel):
    total_bookings: int
    confirmed: int
    cancelled: int
    failed: int
    by_region: Dict[str, int]
    last_updated: datetime


class CapacityReport(BaseModel):
    segment_id: str
    region: str
    slot_start: datetime
    booked_count: int
    max_capacity: int
    utilization_pct: float


class UsageReport(BaseModel):
    total_events: int
    last_24h_events: int
    by_event_type: Dict[str, int]
    by_region: Dict[str, int]
    generated_at: datetime
