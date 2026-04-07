from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from shared.database import get_db
from shared.auth import get_current_user
from models import BookingEvent
from schemas import DashboardStats, CapacityReport, UsageReport

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BookingEvent))
    events = result.scalars().all()

    by_type = {}
    by_region = {}
    for e in events:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        if e.region:
            by_region[e.region] = by_region.get(e.region, 0) + 1

    return DashboardStats(
        total_bookings=len(events),
        confirmed=by_type.get("booking.confirmed", 0),
        cancelled=by_type.get("booking.cancelled", 0),
        failed=by_type.get("booking.failed", 0),
        by_region=by_region,
        last_updated=datetime.utcnow(),
    )


@router.get("/reports/capacity", response_model=list[CapacityReport])
async def capacity_report(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(
            """
            SELECT
                r.segment_id::text AS segment_id,
                r.region,
                r.slot_start,
                r.booked_count,
                r.max_capacity
            FROM (
                SELECT
                    reservation.segment_id,
                    'EU_WEST_IRELAND'::text AS region,
                    date_trunc('hour', reservation.time_slot_start) AS slot_start,
                    COUNT(*) FILTER (
                        WHERE reservation.status NOT IN ('CANCELLED', 'REJECTED')
                    )::int AS booked_count,
                    MAX(segment.max_capacity_per_slot)::int AS max_capacity
                FROM region_ireland.reservations reservation
                JOIN region_ireland.road_segments segment
                  ON segment.id = reservation.segment_id
                GROUP BY reservation.segment_id, date_trunc('hour', reservation.time_slot_start)

                UNION ALL

                SELECT
                    reservation.segment_id,
                    'EU_WEST_UK'::text AS region,
                    date_trunc('hour', reservation.time_slot_start) AS slot_start,
                    COUNT(*) FILTER (
                        WHERE reservation.status NOT IN ('CANCELLED', 'REJECTED')
                    )::int AS booked_count,
                    MAX(segment.max_capacity_per_slot)::int AS max_capacity
                FROM region_uk.reservations reservation
                JOIN region_uk.road_segments segment
                  ON segment.id = reservation.segment_id
                GROUP BY reservation.segment_id, date_trunc('hour', reservation.time_slot_start)

                UNION ALL

                SELECT
                    reservation.segment_id,
                    'EU_WEST_FRANCE'::text AS region,
                    date_trunc('hour', reservation.time_slot_start) AS slot_start,
                    COUNT(*) FILTER (
                        WHERE reservation.status NOT IN ('CANCELLED', 'REJECTED')
                    )::int AS booked_count,
                    MAX(segment.max_capacity_per_slot)::int AS max_capacity
                FROM region_france.reservations reservation
                JOIN region_france.road_segments segment
                  ON segment.id = reservation.segment_id
                GROUP BY reservation.segment_id, date_trunc('hour', reservation.time_slot_start)
            ) AS r
            ORDER BY r.slot_start DESC
            LIMIT 300
            """
        )
    )

    reports: list[CapacityReport] = []
    for row in result.mappings().all():
        booked_count = int(row["booked_count"] or 0)
        max_capacity = int(row["max_capacity"] or 0)
        utilization_pct = (booked_count / max_capacity * 100.0) if max_capacity > 0 else 0.0
        reports.append(
            CapacityReport(
                segment_id=row["segment_id"],
                region=row["region"],
                slot_start=row["slot_start"],
                booked_count=booked_count,
                max_capacity=max_capacity,
                utilization_pct=round(utilization_pct, 2),
            )
        )

    return reports


@router.get("/reports/usage", response_model=UsageReport)
async def usage_report(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_events = await db.scalar(select(func.count(BookingEvent.id))) or 0

    last_24h_cutoff = datetime.utcnow() - timedelta(days=7)
    last_24h_events = (
        await db.scalar(
            select(func.count(BookingEvent.id)).where(BookingEvent.created_at >= last_24h_cutoff)
        )
        or 0
    )

    by_type_result = await db.execute(
        select(BookingEvent.event_type, func.count(BookingEvent.id)).group_by(BookingEvent.event_type)
    )
    by_event_type = {event_type: count for event_type, count in by_type_result.all()}

    by_region_result = await db.execute(
        select(BookingEvent.region, func.count(BookingEvent.id))
        .where(BookingEvent.region.is_not(None))
        .group_by(BookingEvent.region)
    )
    by_region = {region: count for region, count in by_region_result.all() if region}

    recent_footfall_pct = round(last_24h_events / total_events * 100.0, 1) if total_events > 0 else 0.0

    return UsageReport(
        total_events=total_events,
        last_24h_events=last_24h_events,
        recent_footfall_pct=recent_footfall_pct,
        by_event_type=by_event_type,
        by_region=by_region,
        generated_at=datetime.utcnow(),
    )
