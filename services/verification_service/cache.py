import json
from datetime import datetime, timezone
from shared.redis_client import get_redis

CACHE_PREFIX = "active_booking"


async def cache_active_booking(plate_number: str, booking_data: dict, ttl_seconds: int = 3600):
    redis = await get_redis()
    key = f"{CACHE_PREFIX}:{plate_number}"
    await redis.setex(key, ttl_seconds, json.dumps(booking_data, default=str))


async def get_cached_booking(plate_number: str) -> dict | None:
    redis = await get_redis()
    key = f"{CACHE_PREFIX}:{plate_number}"
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None


async def invalidate_booking(plate_number: str):
    redis = await get_redis()
    key = f"{CACHE_PREFIX}:{plate_number}"
    await redis.delete(key)
