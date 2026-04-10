import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from models import Booking, SegmentReservation
from saga import execute_booking_saga
from routing import resolve_route, REGION_SCHEMA_MAP
from shared.messaging import publish_event
from shared.exceptions import BookingNotFoundError, SagaRollbackError, RouteNotFoundError, RegionUnavailableError

logger = logging.getLogger(__name__)


async def _get_driver_plate_number(db: AsyncSession, driver_id: str) -> str | None:
    result = await db.execute(
        text(
            """
            SELECT plate_number
            FROM auth.users
            WHERE id::text = :driver_id
            LIMIT 1
            """
        ),
        {"driver_id": driver_id},
    )
    return result.scalar_one_or_none()


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
    resolved_plate_number = plate_number or await _get_driver_plate_number(db, driver_id)
    departure_time = departure_time.replace(tzinfo=None) if departure_time.tzinfo else departure_time
    booking = Booking(
        id=booking_id,
        driver_id=driver_id,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        plate_number=resolved_plate_number,
        departure_time=departure_time,
        status="SAGA_IN_PROGRESS",
        estimated_duration_minutes=None,
    )
    db.add(booking)
    await db.flush()

    try:
        saga_result = await execute_booking_saga(
            db=db,
            booking_id=booking_id,
            driver_id=driver_id,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            departure_time=departure_time,
            plate_number=resolved_plate_number,
        )

        estimated_minutes = 60
        if isinstance(saga_result, dict):
            estimated_minutes = int(saga_result.get("estimated_duration_minutes") or estimated_minutes)

        booking.estimated_duration_minutes = max(1, estimated_minutes)
        booking.status = "CONFIRMED"
        await db.commit()
        await db.refresh(booking)
    except RegionUnavailableError:
        booking.status = "REJECTED"
        db.add(booking)
        await db.commit()
        raise
    except SagaRollbackError:
        booking.status = "REJECTED"
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        raise
    except Exception as e:
        booking.status = "REJECTED"
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        raise SagaRollbackError(str(e)) from e

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
    if booking.status == "CANCELLED":
        return booking

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

    plate_number = booking.plate_number or await _get_driver_plate_number(db, driver_id)
    try:
        await publish_event(
            routing_key="booking.cancelled",
            payload={
                "event_type": "booking.cancelled",
                "booking_id": booking.id,
                "driver_id": driver_id,
                "plate_number": plate_number,
                "departure_time": booking.departure_time.isoformat(),
            },
        )
    except Exception as e:
        # Cancellation is committed; keep API success and log async side-effect failure.
        logger.error(f"Failed to publish booking.cancelled for {booking.id}: {e}")

    return booking


async def get_driver_bookings(db: AsyncSession, driver_id: str) -> list[Booking]:
    result = await db.execute(select(Booking).where(Booking.driver_id == driver_id))
    return result.scalars().all()


async def preview_route(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    departure_time: datetime,
) -> dict:
    departure_time = departure_time.replace(tzinfo=None) if departure_time.tzinfo else departure_time

    segments, estimated_duration_minutes = await resolve_route(
        db=db,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=destination_lat,
        dest_lng=destination_lng,
        departure_time=departure_time,
    )

    if not segments:
        raise RouteNotFoundError("No valid path found between origin and destination")

    preview_segments: list[dict] = []
    region_chain: list[str] = []

    for seg in segments:
        region = seg["region"]
        schema = REGION_SCHEMA_MAP[region]
        row = await db.execute(
            text(f"SELECT name FROM {schema}.road_segments WHERE id::text = :sid"),
            {"sid": seg["segment_id"]},
        )
        segment_name = row.scalar_one_or_none() or seg["segment_id"][:8]

        if not region_chain or region_chain[-1] != region:
            region_chain.append(region)

        preview_segments.append(
            {
                "segment_id": seg["segment_id"],
                "segment_name": segment_name,
                "region": region,
                "distance_km": round(float(seg.get("distance_km", 0.0)), 2),
                "duration_minutes": int(seg.get("duration_minutes", 0)),
                "slot_start": seg["slot_start"],
                "slot_end": seg["slot_end"],
                "start_lat": seg.get("start_lat"),
                "start_lng": seg.get("start_lng"),
                "end_lat": seg.get("end_lat"),
                "end_lng": seg.get("end_lng"),
            }
        )

    return {
        "route_available": True,
        "reason": None,
        "estimated_duration_minutes": int(estimated_duration_minutes),
        "region_chain": region_chain,
        "segments": preview_segments,
    }