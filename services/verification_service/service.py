"""
Verification Service — core business logic.

Performance contract: <100 ms P95
Strategy:
  1. Redis cache lookup  (~1 ms)
  2. If miss → Aurora read-replica SQL query with indexed plate lookup  (~5-20 ms)
  3. If still nothing → return not_authorized

The cache is warmed by the RabbitMQ consumer (consumer.py) which listens on
`booking.confirmed` and `booking.cancelled` events published by the Booking Service.
This means most enforcement checks are pure cache hits and never touch the DB.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from cache import cache_active_booking, get_cached_booking, count_active_booking_keys, count_all_keys
from schemas import VerificationResult, CacheStatsResponse

logger = logging.getLogger(__name__)

# A journey is valid from departure_time up to departure_time + JOURNEY_WINDOW_HOURS
JOURNEY_WINDOW_HOURS = 2


def _build_authorized_result(plate: str, row, source: str) -> VerificationResult:
    booking_id = str(row["id"])
    departure = row["departure_time"]
    window_end = departure + timedelta(hours=JOURNEY_WINDOW_HOURS)
    return VerificationResult(
        plate_number=plate,
        is_authorized=True,
        booking_id=booking_id,
        driver_id=str(row["driver_id"]),
        status=row["status"],
        departure_time=departure,
        journey_window_end=window_end,
        segments=row.get("segments", []),
        message=f"Active booking found ({source})",
        source=source,
        checked_at=datetime.utcnow(),
    )


async def _lookup_db(db: AsyncSession, plate: str) -> VerificationResult | None:
    """
    Read-replica SQL fallback.

    The query joins bookings → auth.users on driver_id and filters:
      - plate matches
      - booking is CONFIRMED
      - current time is within the journey window

    The index on (plate_number, departure_time) in auth.users makes this fast
    even at millions of rows.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(hours=JOURNEY_WINDOW_HOURS)

    result = await db.execute(
        text("""
            SELECT
                b.id,
                b.driver_id,
                b.status,
                b.departure_time,
                b.origin_lat,
                b.origin_lng,
                b.destination_lat,
                b.destination_lng
            FROM public.bookings b
            JOIN auth.users u ON u.id::text = b.driver_id::text
            WHERE u.plate_number = :plate
              AND b.status = 'CONFIRMED'
              AND b.departure_time >= :window_start
              AND b.departure_time <= :now
            ORDER BY b.departure_time DESC
            LIMIT 1
        """),
        {"plate": plate, "now": now, "window_start": window_start},
    )
    row = result.mappings().fetchone()
    if not row:
        return None

    result_obj = _build_authorized_result(plate, dict(row), "database")

    # Warm the cache so the next check is a hit
    await cache_active_booking(plate, {
        "booking_id": result_obj.booking_id,
        "driver_id": result_obj.driver_id,
        "status": result_obj.status,
        "departure_time": result_obj.departure_time.isoformat() if result_obj.departure_time else None,
        "journey_window_end": result_obj.journey_window_end.isoformat() if result_obj.journey_window_end else None,
        "segments": result_obj.segments,
    })
    return result_obj


async def verify_plate(db: AsyncSession, plate: str) -> VerificationResult:
    now = datetime.utcnow()

    # ── Step 1: Cache-first ────────────────────────────────────────────────
    cached = await get_cached_booking(plate)
    if cached:
        # Validate that the journey window has not passed even if TTL is still alive
        window_end_raw = cached.get("journey_window_end")
        if window_end_raw:
            try:
                window_end = datetime.fromisoformat(str(window_end_raw))
                if now > window_end:
                    # Journey has ended — treat as expired
                    from cache import invalidate_booking
                    await invalidate_booking(plate)
                    # Fall through to DB
                    cached = None
            except Exception:
                pass

    if cached:
        departure_raw = cached.get("departure_time")
        window_end_raw = cached.get("journey_window_end")
        return VerificationResult(
            plate_number=plate,
            is_authorized=True,
            booking_id=cached.get("booking_id"),
            driver_id=cached.get("driver_id"),
            status=cached.get("status"),
            departure_time=datetime.fromisoformat(departure_raw) if departure_raw else None,
            journey_window_end=datetime.fromisoformat(window_end_raw) if window_end_raw else None,
            segments=cached.get("segments", []),
            message="Active booking found (cache)",
            source="cache",
            checked_at=now,
        )

    # ── Step 2: DB read-replica fallback ──────────────────────────────────
    db_result = await _lookup_db(db, plate)
    if db_result:
        return db_result

    # ── Step 3: Not found ─────────────────────────────────────────────────
    return VerificationResult(
        plate_number=plate,
        is_authorized=False,
        message="No active booking found for this vehicle",
        source="not_found",
        checked_at=now,
    )


async def verify_plates_batch(db: AsyncSession, plates: list[str]) -> list[VerificationResult]:
    """
    Resolve multiple plates concurrently. Cache hits are free; DB lookups
    are issued in parallel up to the asyncio event loop limit.
    """
    tasks = [verify_plate(db, plate) for plate in plates]
    return await asyncio.gather(*tasks)


async def get_cache_stats() -> CacheStatsResponse:
    active_keys = await count_active_booking_keys()
    total_keys = await count_all_keys()
    return CacheStatsResponse(
        active_booking_keys=active_keys,
        total_redis_keys=total_keys,
        checked_at=datetime.utcnow(),
    )