import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from shared.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    origin_lat: Mapped[float]
    origin_lng: Mapped[float]
    destination_lat: Mapped[float]
    destination_lng: Mapped[float]
    plate_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SegmentReservation(Base):
    __tablename__ = "segment_reservations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("bookings.id"), nullable=False)
    segment_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    time_slot_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_slot_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)