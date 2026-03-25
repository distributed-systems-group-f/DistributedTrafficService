from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ActiveBooking(BaseModel):
    booking_id: str
    driver_id: str
    plate_number: str
    status: str
    departure_time: datetime
    segments: list = []
