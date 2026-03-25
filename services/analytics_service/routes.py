from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from shared.database import get_db
from shared.auth import get_current_user
from models import BookingEvent
from schemas import DashboardStats

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


@router.get("/reports/capacity")
async def capacity_report(current_user: dict = Depends(get_current_user)):
    return {"message": "Capacity report placeholder", "segments": []}


@router.get("/reports/usage")
async def usage_report(current_user: dict = Depends(get_current_user)):
    return {"message": "Usage report placeholder"}
