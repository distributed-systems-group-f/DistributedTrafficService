import logging
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session_factory
from models import BookingEvent
import uuid

logger = logging.getLogger(__name__)


async def record_event(event_type: str, booking_id: str, driver_id: str, **kwargs):
    factory = get_session_factory()
    async with factory() as db:
        event = BookingEvent(
            id=str(uuid.uuid4()),
            booking_id=booking_id,
            driver_id=driver_id,
            event_type=event_type,
            region=kwargs.get("region"),
            segment_id=kwargs.get("segment_id"),
        )
        db.add(event)
        await db.commit()
        logger.info(f"Recorded analytics event: {event_type} for booking {booking_id}")
