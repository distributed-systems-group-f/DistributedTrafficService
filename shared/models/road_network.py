from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Region(str, Enum):
    EU_WEST_IRELAND = "EU_WEST_IRELAND"
    EU_WEST_UK = "EU_WEST_UK"
    EU_WEST_FRANCE = "EU_WEST_FRANCE"


REGION_SCHEMA_MAP = {
    Region.EU_WEST_IRELAND: "region_ireland",
    Region.EU_WEST_UK: "region_uk",
    Region.EU_WEST_FRANCE: "region_france",
}


class RoadSegment(BaseModel):
    id: str
    name: str
    region: Region
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    max_capacity_per_slot: int = 100


class SegmentCapacity(BaseModel):
    segment_id: str
    region: Region
    time_slot_start: datetime
    time_slot_end: datetime
    booked_count: int
    max_capacity: int

    @property
    def available(self) -> int:
        return self.max_capacity - self.booked_count

    @property
    def is_full(self) -> bool:
        return self.booked_count >= self.max_capacity


class TimeSlot(BaseModel):
    segment_id: str
    start_time: datetime
    end_time: datetime
    booked_count: int = 0
    max_capacity: int = 100
