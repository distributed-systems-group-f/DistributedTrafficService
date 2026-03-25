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
