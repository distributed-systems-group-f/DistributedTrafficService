from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationOut(BaseModel):
    id: str
    user_id: str
    message: str
    channel: str
    sent_at: datetime
    read: bool = False
