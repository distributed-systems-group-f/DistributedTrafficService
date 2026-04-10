"""
Saga Reconciler — Failure Recovery & Partition Merge Handler

This background job addresses two checklist requirements:

1. REPLICA RECOVERY / TOTAL FAILURE:
   After a node crash or total restart, bookings may be stuck in
   SAGA_IN_PROGRESS if the saga orchestrator died mid-flight.
   The reconciler finds these orphaned bookings and either:
     - Marks them REJECTED (if no reservations were committed), or
     - Attempts to complete/roll back based on reservation state.

2. PARTITION MERGE:
   After a network partition heals between two VMs, the local bookings
   table and the regional reservation tables may be inconsistent.
   The reconciler detects and resolves three classes of conflict:
     a) Booking is CONFIRMED but regional reservations are missing
        → roll back to CANCELLED (reservation was lost in the partition)
     b) Booking is SAGA_IN_PROGRESS with partial reservations
        → cancel all reservations, mark booking REJECTED
     c) Regional reservations exist for a booking that was REJECTED/CANCELLED
        → clean up the orphaned reservations (compensating tx was lost)

Runs once on startup (recovers from crashes) and then every
RECONCILE_INTERVAL_SECONDS (heals partitions over time).
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session_factory, get_engine
from shared.messaging import publish_event

logger = logging.getLogger(__name__)

# How old a SAGA_IN_PROGRESS booking must be before we consider it orphaned.
# This avoids racing with an in-flight saga that is still executing.
ORPHAN_THRESHOLD_SECONDS = int(os.environ.get("RECONCILE_ORPHAN_THRESHOLD_SECONDS", "60"))

# How often the reconciler runs (seconds).
RECONCILE_INTERVAL_SECONDS = int(os.environ.get("RECONCILE_INTERVAL_SECONDS", "120"))

REGION_SCHEMAS = ["region_ireland", "region_uk", "region_france"]


async def _reconcile_orphaned_sagas(db: AsyncSession) -> int:
    """
    Find bookings stuck in SAGA_IN_PROGRESS longer than the orphan threshold.
    For each one, check if any reservations were committed:
      - If yes: cancel them (compensating transaction) and mark booking REJECTED.
      - If no:  just mark booking REJECTED.
    Returns the number of bookings reconciled.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=ORPHAN_THRESHOLD_SECONDS)

    result = await db.execute(
        text("""
            SELECT id, driver_id, plate_number
            FROM public.bookings
            WHERE status = 'SAGA_IN_PROGRESS'
              AND created_at < :cutoff
        """),
        {"cutoff": cutoff},
    )
    orphans = result.mappings().all()

    if not orphans:
        return 0

    logger.warning(f"Reconciler found {len(orphans)} orphaned SAGA_IN_PROGRESS booking(s)")

    reconciled = 0
    for orphan in orphans:
        booking_id = str(orphan["id"])
        driver_id = str(orphan["driver_id"])
        plate_number = orphan.get("plate_number")

        # Cancel any regional reservations that were partially committed
        for schema in REGION_SCHEMAS:
            await db.execute(
                text(f"""
                    UPDATE {schema}.reservations
                    SET status = 'CANCELLED'
                    WHERE booking_id = :bid AND status NOT IN ('CANCELLED')
                """),
                {"bid": booking_id},
            )

        # Cancel segment_reservations in the public schema too
        await db.execute(
            text("""
                UPDATE public.segment_reservations
                SET status = 'CANCELLED'
                WHERE booking_id = :bid AND status NOT IN ('CANCELLED')
            """),
            {"bid": booking_id},
        )

        # Mark the booking as REJECTED
        await db.execute(
            text("""
                UPDATE public.bookings
                SET status = 'REJECTED', updated_at = NOW()
                WHERE id = :bid
            """),
            {"bid": booking_id},
        )

        await db.commit()

        # Publish failure event so notification/analytics services are informed
        try:
            await publish_event(
                routing_key="booking.failed",
                payload={
                    "event_type": "booking.failed",
                    "booking_id": booking_id,
                    "driver_id": driver_id,
                    "plate_number": plate_number,
                    "reason": "Reconciled: saga was orphaned after node failure",
                },
            )
        except Exception as e:
            logger.error(f"Reconciler: failed to publish event for {booking_id}: {e}")

        reconciled += 1
        logger.info(f"Reconciled orphaned booking {booking_id} → REJECTED")

    return reconciled


async def _reconcile_partition_inconsistencies(db: AsyncSession) -> int:
    """
    After a network partition heals, the bookings table and the regional
    reservation tables may disagree. This function detects and fixes three
    classes of inconsistency:

    Case A — CONFIRMED booking with missing regional reservations:
       The booking was confirmed locally but the peer's reservations were
       lost (peer was partitioned when compensating tx fired, or reservation
       was never committed). We cancel the booking because it's no longer
       backed by actual road capacity.

    Case B — REJECTED/CANCELLED booking with lingering regional reservations:
       The compensating transaction didn't reach the regional DB (peer was
       partitioned). We clean up the orphaned reservations to free capacity.

    Returns total number of corrections made.
    """
    corrections = 0

    # ── Case A: CONFIRMED bookings with no matching regional reservations ──
    # For each CONFIRMED booking, check that at least one regional reservation
    # exists with status CONFIRMED. If none do, the booking is dangling.
    confirmed_result = await db.execute(
        text("""
            SELECT b.id, b.driver_id, b.plate_number
            FROM public.bookings b
            WHERE b.status = 'CONFIRMED'
              AND b.created_at < NOW() - INTERVAL '2 minutes'
              AND NOT EXISTS (
                  SELECT 1 FROM public.segment_reservations sr
                  WHERE sr.booking_id = b.id AND sr.status = 'CONFIRMED'
              )
        """)
    )
    dangling_confirmed = confirmed_result.mappings().all()

    for row in dangling_confirmed:
        booking_id = str(row["id"])
        driver_id = str(row["driver_id"])
        plate_number = row.get("plate_number")

        # Also clean up any regional reservations just in case
        for schema in REGION_SCHEMAS:
            await db.execute(
                text(f"""
                    UPDATE {schema}.reservations
                    SET status = 'CANCELLED'
                    WHERE booking_id = :bid AND status NOT IN ('CANCELLED')
                """),
                {"bid": booking_id},
            )

        await db.execute(
            text("""
                UPDATE public.bookings
                SET status = 'CANCELLED', updated_at = NOW()
                WHERE id = :bid
            """),
            {"bid": booking_id},
        )
        await db.commit()

        try:
            await publish_event(
                routing_key="booking.cancelled",
                payload={
                    "event_type": "booking.cancelled",
                    "booking_id": booking_id,
                    "driver_id": driver_id,
                    "plate_number": plate_number,
                    "reason": "Reconciled: reservations lost during partition",
                },
            )
        except Exception:
            pass

        corrections += 1
        logger.info(
            f"Partition reconciler: CONFIRMED booking {booking_id} had no reservations → CANCELLED"
        )

    # ── Case B: CANCELLED/REJECTED bookings with lingering regional reservations ──
    for schema in REGION_SCHEMAS:
        lingering_result = await db.execute(
            text(f"""
                SELECT DISTINCT r.booking_id::text AS booking_id
                FROM {schema}.reservations r
                JOIN public.bookings b ON b.id = r.booking_id
                WHERE r.status NOT IN ('CANCELLED')
                  AND b.status IN ('CANCELLED', 'REJECTED')
            """)
        )
        lingering = lingering_result.mappings().all()

        for row in lingering:
            booking_id = row["booking_id"]
            await db.execute(
                text(f"""
                    UPDATE {schema}.reservations
                    SET status = 'CANCELLED'
                    WHERE booking_id = :bid AND status NOT IN ('CANCELLED')
                """),
                {"bid": booking_id},
            )
            await db.commit()
            corrections += 1
            logger.info(
                f"Partition reconciler: cleaned orphaned reservations in {schema} "
                f"for cancelled booking {booking_id}"
            )

    return corrections


async def run_reconciliation_once() -> dict:
    """Execute one reconciliation pass. Returns counts for logging/API."""
    session_factory = get_session_factory()
    async with session_factory() as db:
        orphans = await _reconcile_orphaned_sagas(db)
        partitions = await _reconcile_partition_inconsistencies(db)
    return {"orphaned_sagas_fixed": orphans, "partition_inconsistencies_fixed": partitions}


async def reconciliation_loop():
    """
    Background loop: runs immediately on startup (crash recovery),
    then repeats every RECONCILE_INTERVAL_SECONDS (partition healing).
    """
    # Wait a few seconds on startup for DB connections to be ready
    await asyncio.sleep(5)

    while True:
        try:
            result = await run_reconciliation_once()
            total = result["orphaned_sagas_fixed"] + result["partition_inconsistencies_fixed"]
            if total > 0:
                logger.warning(f"Reconciliation pass complete: {result}")
            else:
                logger.debug("Reconciliation pass: no issues found")
        except Exception as e:
            logger.error(f"Reconciliation pass failed: {e}")

        await asyncio.sleep(RECONCILE_INTERVAL_SECONDS)