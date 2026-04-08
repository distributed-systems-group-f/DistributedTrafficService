import logging
import os
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from models import SegmentReservation
from shared.messaging import publish_event
from shared.exceptions import CapacityExceededError, SagaRollbackError, SegmentNotFoundError
from distributed_lock import segment_lock
from capacity import check_capacity, reserve_segment, release_segment
from routing import resolve_route, REGION_SCHEMA_MAP

logger = logging.getLogger(__name__)

# Which regions this VM owns — comma-separated for multiple regions.
# e.g. "EU_WEST_UK,EU_WEST_FRANCE" means this VM handles both UK and France locally.
# All other regions are routed to the peer.
LOCAL_REGIONS = {
    r.strip()
    for r in os.environ.get("LOCAL_REGION", "EU_WEST_IRELAND").split(",")
    if r.strip()
}

# HTTP base URL of the peer booking service (e.g. http://VM2_IP:8002)
# Empty string means single-VM mode — all regions handled locally
PEER_BOOKING_URL = os.environ.get("PEER_BOOKING_URL", "").rstrip("/")

PEER_TIMEOUT_SECONDS = 10.0


async def _peer_reserve(
    booking_id: str,
    segment_id: str,
    region: str,
    driver_id: str,
    slot_start: datetime,
    slot_end: datetime,
) -> str:
    """Call the peer VM to reserve a segment in its local DB. Returns reservation_id."""
    async with httpx.AsyncClient(timeout=PEER_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{PEER_BOOKING_URL}/bookings/peer/reserve",
            json={
                "booking_id": booking_id,
                "segment_id": segment_id,
                "region": region,
                "driver_id": driver_id,
                "slot_start": slot_start.isoformat(),
                "slot_end": slot_end.isoformat(),
            },
        )
        if resp.status_code == 409:
            raise CapacityExceededError(f"Peer: segment {segment_id} is full")
        resp.raise_for_status()
        return resp.json()["reservation_id"]


async def _peer_release(booking_id: str) -> None:
    """Ask the peer VM to cancel all reservations for this booking (compensating tx)."""
    try:
        async with httpx.AsyncClient(timeout=PEER_TIMEOUT_SECONDS) as client:
            await client.delete(f"{PEER_BOOKING_URL}/bookings/peer/reserve/{booking_id}")
    except Exception as e:
        logger.error(f"Peer rollback failed for booking {booking_id}: {e}")


def _is_local(region: str) -> bool:
    """True if this region is owned by the local VM, or if no peer is configured."""
    if not PEER_BOOKING_URL:
        return True  # single-VM mode — handle everything locally
    return region in LOCAL_REGIONS


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
    - Single-region route: local DB transaction only.
    - Cross-region route: local segments via local DB, remote segments via peer HTTP.
    - On any failure: compensating transactions roll back all reservations.
    """
    route_segments, estimated_duration_minutes = await resolve_route(
        db=db,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        departure_time=departure_time,
    )

    regions_involved = [seg["region"] for seg in route_segments]
    is_cross_region = any(not _is_local(r) for r in regions_involved)

    logger.info(
        f"[SAGA:{booking_id[:8]}] START — "
        f"segments={len(route_segments)}, regions={regions_involved}, "
        f"cross_region={is_cross_region}, local_regions={LOCAL_REGIONS}, peer={PEER_BOOKING_URL or 'none'}"
    )

    reserved = []
    peer_reserved = False  # track whether we made any peer calls

    try:
        for i, seg in enumerate(route_segments, 1):
            schema = REGION_SCHEMA_MAP[seg["region"]]
            slot_key = seg["slot_start"].isoformat()

            if _is_local(seg["region"]):
                # ── Local segment: acquire lock + write to local DB ──────────
                logger.info(
                    f"[SAGA:{booking_id[:8]}] Step {i}/{len(route_segments)} — "
                    f"LOCAL reserve segment={seg['segment_id'][:8]} region={seg['region']} slot={slot_key}"
                )
                async with segment_lock(seg["segment_id"], slot_key):
                    try:
                        cap = await check_capacity(db, schema, seg["segment_id"], seg["slot_start"])
                        if cap["booked"] >= cap["max"]:
                            raise CapacityExceededError(
                                f"Segment {seg['segment_id']} is full for slot {slot_key}"
                            )
                    except SegmentNotFoundError:
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
                logger.info(
                    f"[SAGA:{booking_id[:8]}] Step {i}/{len(route_segments)} — "
                    f"LOCAL reserved OK res_id={res_id[:8]}"
                )
            else:
                # ── Remote segment: call peer VM ─────────────────────────────
                logger.info(
                    f"[SAGA:{booking_id[:8]}] Step {i}/{len(route_segments)} — "
                    f"PEER reserve segment={seg['segment_id'][:8]} region={seg['region']} "
                    f"peer={PEER_BOOKING_URL} slot={slot_key}"
                )
                res_id = await _peer_reserve(
                    booking_id=booking_id,
                    segment_id=seg["segment_id"],
                    region=seg["region"],
                    driver_id=driver_id,
                    slot_start=seg["slot_start"],
                    slot_end=seg["slot_end"],
                )
                peer_reserved = True
                logger.info(
                    f"[SAGA:{booking_id[:8]}] Step {i}/{len(route_segments)} — "
                    f"PEER reserved OK res_id={res_id[:8]}"
                )

            reserved.append({
                "reservation_id": res_id,
                "segment_id": seg["segment_id"],
                "region": seg["region"],
                "schema": schema,
                "slot_start": seg["slot_start"],
                "slot_end": seg["slot_end"],
                "duration_minutes": seg.get("duration_minutes", 0),
                "is_local": _is_local(seg["region"]),
            })

        await db.commit()

        logger.info(
            f"[SAGA:{booking_id[:8]}] COMMITTED — "
            f"all {len(reserved)} segments reserved, publishing booking.confirmed"
        )

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
        logger.error(
            f"[SAGA:{booking_id[:8]}] FAILED — reason='{e}'. "
            f"Rolling back {len(reserved)} reserved segments "
            f"(local={sum(1 for r in reserved if r.get('is_local', True))}, "
            f"peer={sum(1 for r in reserved if not r.get('is_local', True))})"
        )
        await db.rollback()

        # Compensating transactions — local rollback
        for r in reserved:
            if r.get("is_local", True):
                try:
                    await release_segment(db, r["schema"], booking_id)
                    await db.commit()
                    logger.info(f"[SAGA:{booking_id[:8]}] COMPENSATE LOCAL — released segment={r['segment_id'][:8]}")
                except Exception as rollback_err:
                    logger.error(f"[SAGA:{booking_id[:8]}] COMPENSATE LOCAL FAILED — {rollback_err}")

        # Compensating transactions — peer rollback
        if peer_reserved and PEER_BOOKING_URL:
            logger.info(f"[SAGA:{booking_id[:8]}] COMPENSATE PEER — sending rollback to {PEER_BOOKING_URL}")
            await _peer_release(booking_id)
            logger.info(f"[SAGA:{booking_id[:8]}] COMPENSATE PEER — done")

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