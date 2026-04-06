from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db
from shared.auth import get_current_user
from shared.exceptions import BookingNotFoundError, SagaRollbackError, RouteNotFoundError
from schemas import (
    BookingCreateRequest,
    BookingOut,
    PeerReserveRequest,
    ReservationOut,
    RoutePreviewRequest,
    RoutePreviewOut,
)
from routing import REGION_SCHEMA_MAP
from distributed_lock import segment_lock
from capacity import check_capacity, reserve_segment, release_segment
from shared.exceptions import CapacityExceededError
import service

router = APIRouter()


@router.get("/my/journeys", response_model=list[BookingOut])
async def my_journeys(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookings = await service.get_driver_bookings(db, current_user["sub"])
    return [
        BookingOut(
            booking_id=b.id,
            status=b.status,
            estimated_duration_minutes=b.estimated_duration_minutes,
            created_at=b.created_at,
        )
        for b in bookings
    ]


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        booking = await service.create_booking(
            db=db,
            driver_id=current_user["sub"],
            origin_lat=req.origin_lat,
            origin_lng=req.origin_lng,
            dest_lat=req.destination_lat,
            dest_lng=req.destination_lng,
            departure_time=req.departure_time,
            plate_number=req.plate_number,
        )
        return BookingOut(
            booking_id=booking.id,
            status=booking.status,
            estimated_duration_minutes=booking.estimated_duration_minutes,
            created_at=booking.created_at,
        )
    except SagaRollbackError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/preview-route", response_model=RoutePreviewOut)
async def preview_route(
    req: RoutePreviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.preview_route(
            db=db,
            origin_lat=req.origin_lat,
            origin_lng=req.origin_lng,
            destination_lat=req.destination_lat,
            destination_lng=req.destination_lng,
            departure_time=req.departure_time,
        )
    except RouteNotFoundError as e:
        return RoutePreviewOut(route_available=False, reason=str(e))


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        booking = await service.get_booking(db, booking_id)
        return BookingOut(
            booking_id=booking.id,
            status=booking.status,
            estimated_duration_minutes=booking.estimated_duration_minutes,
            created_at=booking.created_at,
        )
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{booking_id}", response_model=BookingOut)
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        booking = await service.cancel_booking(db, booking_id, current_user["sub"])
        return BookingOut(
            booking_id=booking.id,
            status=booking.status,
            estimated_duration_minutes=booking.estimated_duration_minutes,
            created_at=booking.created_at,
        )
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ---------------------------------------------------------------------------
# Internal peer endpoints — called by the remote VM's saga, no auth required
# ---------------------------------------------------------------------------

@router.post("/peer/reserve", status_code=201)
async def peer_reserve(
    req: PeerReserveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reserve a segment on behalf of a remote VM's saga."""
    schema = REGION_SCHEMA_MAP.get(req.region)
    if not schema:
        raise HTTPException(status_code=400, detail=f"Unknown region: {req.region}")

    async with segment_lock(req.segment_id, req.slot_start.isoformat()):
        cap = await check_capacity(db, schema, req.segment_id, req.slot_start)
        if cap["booked"] >= cap["max"]:
            raise HTTPException(status_code=409, detail=f"Segment {req.segment_id} is full")

        res_id = await reserve_segment(
            db=db,
            region_schema=schema,
            booking_id=req.booking_id,
            segment_id=req.segment_id,
            driver_id=req.driver_id,
            slot_start=req.slot_start,
            slot_end=req.slot_end,
            status="CONFIRMED",
        )
        await db.commit()

    return {"reservation_id": res_id, "status": "CONFIRMED"}


@router.delete("/peer/reserve/{booking_id}", status_code=200)
async def peer_release(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Roll back all reservations for a booking on this peer (compensating transaction)."""
    for schema in REGION_SCHEMA_MAP.values():
        await release_segment(db, schema, booking_id)
    await db.commit()
    return {"booking_id": booking_id, "status": "CANCELLED"}