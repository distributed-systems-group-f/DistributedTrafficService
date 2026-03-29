import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Booking, SegmentReservation
from saga import execute_booking_saga
from shared.exceptions import BookingNotFoundError


async def create_booking(
    db: AsyncSession,
    driver_id: str,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    departure_time: datetime,
    plate_number: str | None = None,
) -> Booking:
    booking_id = str(uuid.uuid4())
    departure_time = departure_time.replace(tzinfo=None) if departure_time.tzinfo else departure_time
    booking = Booking(
        id=booking_id,
        driver_id=driver_id,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        departure_time=departure_time,
        status="SAGA_IN_PROGRESS",
        estimated_duration_minutes=60,
    )
    db.add(booking)
    await db.flush()

    try:
        await execute_booking_saga(
            db=db,
            booking_id=booking_id,
            driver_id=driver_id,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            departure_time=departure_time,
            plate_number=plate_number,
        )
        booking.status = "CONFIRMED"
        await db.commit()
        await db.refresh(booking)
    except Exception:
        # Saga already rolled back — the booking object is detached.
        # Re-add it so we can persist the REJECTED status.
        booking.status = "REJECTED"
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

    return booking


async def get_booking(db: AsyncSession, booking_id: str) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise BookingNotFoundError(f"Booking {booking_id} not found")
    return booking


async def cancel_booking(db: AsyncSession, booking_id: str, driver_id: str) -> Booking:
    booking = await get_booking(db, booking_id)
    if booking.driver_id != driver_id:
        raise PermissionError("Cannot cancel another driver's booking")
    await db.execute(
        update(Booking).where(Booking.id == booking_id).values(status="CANCELLED")
    )
    await db.execute(
        update(SegmentReservation)
        .where(SegmentReservation.booking_id == booking_id)
        .values(status="CANCELLED")
    )
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_driver_bookings(db: AsyncSession, driver_id: str) -> list[Booking]:
    result = await db.execute(select(Booking).where(Booking.driver_id == driver_id))
    return result.scalars().all()