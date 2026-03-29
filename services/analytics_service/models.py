import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from shared.database import Base


class BookingEvent(Base):
    __tablename__ = "booking_events"
    __table_args__ = {"schema": "analytics"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    driver_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)