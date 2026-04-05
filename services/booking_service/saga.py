import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models import SegmentReservation
from shared.messaging import publish_event
from shared.exceptions import CapacityExceededError, SagaRollbackError, SegmentNotFoundError
from distributed_lock import segment_lock
from capacity import check_capacity, reserve_segment, release_segment
from routing import resolve_route, REGION_SCHEMA_MAP

logger = logging.getLogger(__name__)


async def execute_booking_saga(
    db: AsyncSession,
    booking_id: str,
    driver_id: str,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    departure_time: datetime,
    plate_number: str | None = None,
) -> dict:
    """
    Executes the booking saga.
    - Single region: local transaction
    - Multi-region: saga with compensating transactions on failure
    """
    route_segments, estimated_duration_minutes = await resolve_route(
        db=db,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        departure_time=departure_time,
    )
    reserved = []

    try:
        for seg in route_segments:
            schema = REGION_SCHEMA_MAP[seg["region"]]
            slot_key = seg["slot_start"].isoformat()

            async with segment_lock(seg["segment_id"], slot_key):
                try:
                    cap = await check_capacity(db, schema, seg["segment_id"], seg["slot_start"])
                    if cap["booked"] >= cap["max"]:
                        raise CapacityExceededError(
                            f"Segment {seg['segment_id']} is full for slot {slot_key}"
                        )
                except SegmentNotFoundError:
                    # Segment may not exist in seed data — skip gracefully in dev
                    cap = {"slot_start": seg["slot_start"], "slot_end": seg["slot_end"]}

                res_id = await reserve_segment(
                    db=db,
                    region_schema=schema,
                    booking_id=booking_id,
                    segment_id=seg["segment_id"],
                    driver_id=driver_id,
                    slot_start=seg["slot_start"],
                    slot_end=seg["slot_end"],
                    status="CONFIRMED",
                )
                reserved.append({
                    "reservation_id": res_id,
                    "segment_id": seg["segment_id"],
                    "region": seg["region"],
                    "schema": schema,
                    "slot_start": seg["slot_start"],
                    "slot_end": seg["slot_end"],
                    "duration_minutes": seg.get("duration_minutes", 0),
                })

                db.add(
                    SegmentReservation(
                        booking_id=booking_id,
                        segment_id=seg["segment_id"],
                        region=seg["region"],
                        time_slot_start=seg["slot_start"],
                        time_slot_end=seg["slot_end"],
                        status="CONFIRMED",
                    )
                )

        await db.commit()

        # Publish booking confirmed event
        await publish_event(
            routing_key="booking.confirmed",
            payload={
                "event_type": "booking.confirmed",
                "booking_id": booking_id,
                "driver_id": driver_id,
                "plate_number": plate_number,
                "segments": [
                    {"segment_id": r["segment_id"], "region": r["region"]}
                    for r in reserved
                ],
                "departure_time": departure_time.isoformat(),
            },
        )
        return {
            "reservations": reserved,
            "estimated_duration_minutes": estimated_duration_minutes,
        }

    except Exception as e:
        logger.error(f"Saga failed for booking {booking_id}: {e}. Rolling back.")
        await db.rollback()
        # Compensating transactions
        for r in reserved:
            try:
                await release_segment(db, r["schema"], booking_id)
                await db.commit()
            except Exception as rollback_err:
                logger.error(f"Rollback failed: {rollback_err}")

        await publish_event(
            routing_key="booking.failed",
            payload={
                "event_type": "booking.failed",
                "booking_id": booking_id,
                "driver_id": driver_id,
                "plate_number": plate_number,
                "reason": str(e),
            },
        )
        raise SagaRollbackError(str(e)) from e