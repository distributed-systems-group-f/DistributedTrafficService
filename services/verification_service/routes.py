import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, init_db
from shared.auth import get_current_user
from schemas import VerificationResult, BatchVerificationRequest, BatchVerificationResponse, CacheStatsResponse
import service

logger = logging.getLogger(__name__)
router = APIRouter()
init_db()


def _require_enforcement(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Enforcement agents and admins can call verify endpoints.
    Drivers cannot look up other plates.
    """
    role = current_user.get("role", "")
    if role not in ("enforcement_agent", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only enforcement agents and admins can verify plate numbers.",
        )
    return current_user


@router.get(
    "/{plate_number}",
    response_model=VerificationResult,
    summary="Verify a single plate number",
    description=(
        "Returns the active booking status for a vehicle plate in <100 ms. "
        "Cache-first lookup via Redis; falls back to the Aurora read-replica "
        "if the key is missing (cold cache or after a booking event clears it)."
    ),
)
async def verify_plate(
    plate_number: str,
    current_user: dict = Depends(_require_enforcement),
    db: AsyncSession = Depends(get_db),
):
    plate = plate_number.upper().strip()
    result = await service.verify_plate(db, plate)
    logger.info(
        "Plate check: plate=%s authorized=%s source=%s agent=%s",
        plate,
        result.is_authorized,
        result.source,
        current_user.get("sub"),
    )
    return result


@router.post(
    "/batch",
    response_model=BatchVerificationResponse,
    summary="Verify multiple plates in one call",
    description=(
        "Batch lookup for enforcement scenarios where multiple vehicles are "
        "checked at once (e.g. at a checkpoint). Each plate is resolved "
        "independently: cache hit where available, DB fallback otherwise."
    ),
)
async def verify_plates_batch(
    req: BatchVerificationRequest,
    current_user: dict = Depends(_require_enforcement),
    db: AsyncSession = Depends(get_db),
):
    if len(req.plate_numbers) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 plates per batch request.")

    results = await service.verify_plates_batch(db, [p.upper().strip() for p in req.plate_numbers])
    return BatchVerificationResponse(results=results)


@router.get(
    "/_cache/stats",
    response_model=CacheStatsResponse,
    summary="Cache statistics (admin only)",
    description="Returns Redis key counts for monitoring cache warm-up state.",
)
async def cache_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    return await service.get_cache_stats()


@router.delete(
    "/_cache/{plate_number}",
    summary="Manually invalidate a cached plate (admin only)",
)
async def invalidate_cache(plate_number: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    from cache import invalidate_booking
    await invalidate_booking(plate_number.upper().strip())
    return {"invalidated": plate_number.upper().strip()}