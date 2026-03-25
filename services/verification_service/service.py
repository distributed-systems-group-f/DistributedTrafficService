from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from cache import get_cached_booking
from schemas import VerificationResult


async def verify_plate(db: AsyncSession, plate_number: str) -> VerificationResult:
    now = datetime.utcnow()

    # Cache-first lookup
    cached = await get_cached_booking(plate_number)
    if cached:
        return VerificationResult(
            plate_number=plate_number,
            is_authorized=True,
            booking_id=cached.get("booking_id"),
            status=cached.get("status"),
            message="Active booking found (cache hit)",
            checked_at=now,
        )

    # DB fallback
    result = await db.execute(
        text("""
            SELECT b.id, b.status, b.departure_time
            FROM bookings b
            JOIN auth.users u ON u.id = b.driver_id
            WHERE u.plate_number = :plate
              AND b.status = 'CONFIRMED'
              AND b.departure_time <= :now
              AND b.departure_time + INTERVAL '2 hours' >= :now
            ORDER BY b.departure_time DESC
            LIMIT 1
        """),
        {"plate": plate_number, "now": now},
    )
    row = result.fetchone()

    if row:
        return VerificationResult(
            plate_number=plate_number,
            is_authorized=True,
            booking_id=str(row[0]),
            status=row[1],
            message="Active booking found (DB hit)",
            checked_at=now,
        )

    return VerificationResult(
        plate_number=plate_number,
        is_authorized=False,
        message="No active booking found",
        checked_at=now,
    )
