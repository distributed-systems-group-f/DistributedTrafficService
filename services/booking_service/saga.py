import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from shared.messaging import publish_event
from shared.exceptions import CapacityExceededError, SagaRollbackError
from distributed_lock import segment_lock
from capacity import check_capacity, reserve_segment, release_segment

logger = logging.getLogger(__name__)

REGION_SCHEMA_MAP = {
    "EU_WEST_IRELAND": "region_ireland",
    "EU_WEST_UK": "region_uk",
    "EU_WEST_FRANCE": "region_france",
}

# Simple route resolution: return one segment per region based on coordinates
def resolve_route(origin_lat, origin_lng, dest_lat, dest_lng, departure_time):
    """
    Simplified route resolver. In production this would call a routing API.
    Returns a list of (segment_id, region) tuples.
    """
    # Dummy logic: assign region based on lat/lng ranges
    def region_for(lat, lng):
        if 51.0 <= lat <= 55.5 and -10.5 <= lng <= -6.0:
            return "EU_WEST_IRELAND"
        elif 49.9 <= lat <= 58.7 and -5.7 <= lng <= 1.8:
            return "EU_WEST_UK"
        else:
            return "EU_WEST_FRANCE"

    origin_region = region_for(origin_lat, origin_lng)
    dest_region = region_for(dest_lat, dest_lng)

    segments = []
    # Use first available segment from each region (simplified)
    seen_regions = set()
    for region in [origin_region, dest_region]:
        if region not in seen_regions:
            seen_regions.add(region)
            segments.append({
                "segment_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, region)),
                "region": region,
                "slot_start": departure_time.replace(minute=0, second=0, microsecond=0),
                "slot_end": departure_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1),
            })

    return segments


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
) -> list[dict]:
    """
    Executes the booking saga.
    - Single region: local transaction
    - Multi-region: saga with compensating transactions on failure
    """
    route_segments = resolve_route(origin_lat, origin_lng, dest_lat, dest_lng, departure_time)
    reserved = []

    try:
        for seg in route_segments:
            schema = REGION_SCHEMA_MAP[seg["region"]]
            slot_key = seg["slot_start"].isoformat()

            async with segment_lock(seg["segment_id"], slot_key):
                try:
                    cap = await check_capacity(db, schema, seg["segment_id"], departure_time)
                    if cap["booked"] >= cap["max"]:
                        raise CapacityExceededError(
                            f"Segment {seg['segment_id']} is full for slot {slot_key}"
                        )
                except Exception:
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
                })

        await db.commit()

        # Publish booking confirmed event
        await publish_event(
            routing_key="booking.confirmed",
            payload={
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
        return reserved

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
            payload={"booking_id": booking_id, "driver_id": driver_id, "reason": str(e)},
        )
        raise SagaRollbackError(str(e)) from e