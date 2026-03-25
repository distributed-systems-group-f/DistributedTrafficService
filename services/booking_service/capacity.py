from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from shared.exceptions import CapacityExceededError, SegmentNotFoundError

SLOT_DURATION_MINUTES = 60
DEFAULT_CAPACITY = 100


async def check_capacity(
    db: AsyncSession,
    region_schema: str,
    segment_id: str,
    departure_time: datetime,
) -> dict:
    slot_start = departure_time.replace(minute=0, second=0, microsecond=0)
    slot_end = slot_start + timedelta(hours=1)

    seg_result = await db.execute(
        text(f"SELECT max_capacity_per_slot FROM {region_schema}.road_segments WHERE id = :sid"),
        {"sid": segment_id},
    )
    row = seg_result.fetchone()
    if not row:
        raise SegmentNotFoundError(f"Segment {segment_id} not found in {region_schema}")

    max_cap = row[0]

    res_result = await db.execute(
        text(
            f"""
            SELECT COUNT(*) FROM {region_schema}.reservations
            WHERE segment_id = :sid
              AND time_slot_start = :ts
              AND status NOT IN ('CANCELLED', 'REJECTED')
            """
        ),
        {"sid": segment_id, "ts": slot_start},
    )
    booked = res_result.scalar()
    return {"slot_start": slot_start, "slot_end": slot_end, "booked": booked, "max": max_cap}


async def reserve_segment(
    db: AsyncSession,
    region_schema: str,
    booking_id: str,
    segment_id: str,
    driver_id: str,
    slot_start: datetime,
    slot_end: datetime,
    status: str = "PENDING",
) -> str:
    import uuid
    res_id = str(uuid.uuid4())
    await db.execute(
        text(
            f"""
            INSERT INTO {region_schema}.reservations
              (id, booking_id, segment_id, driver_id, time_slot_start, time_slot_end, status)
            VALUES (:id, :bid, :sid, :did, :ts, :te, :st)
            """
        ),
        {
            "id": res_id,
            "bid": booking_id,
            "sid": segment_id,
            "did": driver_id,
            "ts": slot_start,
            "te": slot_end,
            "st": status,
        },
    )
    return res_id


async def release_segment(db: AsyncSession, region_schema: str, booking_id: str) -> None:
    await db.execute(
        text(
            f"UPDATE {region_schema}.reservations SET status = 'CANCELLED' WHERE booking_id = :bid"
        ),
        {"bid": booking_id},
    )
