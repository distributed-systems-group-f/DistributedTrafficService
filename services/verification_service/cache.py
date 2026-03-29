"""
Redis cache layer for the Verification Service.

Key design decisions:
- Key: `active_booking:{PLATE_NUMBER}` (uppercase, normalised)
- TTL: set to the booking's journey-window-end time so stale entries
  self-expire even if no cancellation event arrives (defence-in-depth).
- Fallback TTL: 1 hour for safety when window-end is not calculable.
- Invalidation is event-driven: the RabbitMQ consumer calls
  `invalidate_booking` on booking.cancelled / booking.failed.
"""

import json
import logging
from datetime import datetime, timezone
from shared.redis_client import get_redis

logger = logging.getLogger(__name__)

CACHE_PREFIX = "active_booking"
DEFAULT_TTL_SECONDS = 3600  # 1 hour fallback


def _cache_key(plate_number: str) -> str:
    return f"{CACHE_PREFIX}:{plate_number.upper()}"


async def cache_active_booking(plate_number: str, booking_data: dict, ttl_seconds: int | None = None) -> None:
    """
    Store an active booking for a plate.

    ttl_seconds is computed from the booking's journey window end so the key
    expires naturally even without an explicit invalidation event.
    """
    redis = await get_redis()
    key = _cache_key(plate_number)
    ttl = ttl_seconds or DEFAULT_TTL_SECONDS

    # If journey_window_end is present, use it to derive a tight TTL
    if "journey_window_end" in booking_data and booking_data["journey_window_end"]:
        try:
            window_end = datetime.fromisoformat(str(booking_data["journey_window_end"]))
            now = datetime.utcnow()
            remaining_seconds = int((window_end - now).total_seconds())
            if remaining_seconds > 0:
                ttl = remaining_seconds + 300  # 5-min grace buffer
        except Exception:
            pass  # fall through to default TTL

    await redis.setex(key, ttl, json.dumps(booking_data, default=str))
    logger.debug("Cached booking for plate=%s ttl=%ds", plate_number, ttl)


async def get_cached_booking(plate_number: str) -> dict | None:
    redis = await get_redis()
    key = _cache_key(plate_number)
    data = await redis.get(key)
    if data:
        logger.debug("Cache HIT for plate=%s", plate_number)
        return json.loads(data)
    logger.debug("Cache MISS for plate=%s", plate_number)
    return None


async def invalidate_booking(plate_number: str) -> None:
    redis = await get_redis()
    key = _cache_key(plate_number)
    deleted = await redis.delete(key)
    if deleted:
        logger.info("Cache invalidated for plate=%s", plate_number)
    else:
        logger.debug("Cache invalidation for plate=%s — key was not present", plate_number)


async def count_active_booking_keys() -> int:
    redis = await get_redis()
    keys = await redis.keys(f"{CACHE_PREFIX}:*")
    return len(keys)


async def count_all_keys() -> int:
    redis = await get_redis()
    return await redis.dbsize()