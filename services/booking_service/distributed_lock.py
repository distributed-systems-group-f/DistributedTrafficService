import asyncio
import uuid
from contextlib import asynccontextmanager
from shared.redis_client import get_redis
from shared.exceptions import LockAcquisitionError

LOCK_TIMEOUT_MS = 5000


@asynccontextmanager
async def segment_lock(segment_id: str, slot_id: str):
    """Redis-based distributed lock for a specific segment+slot combination."""
    redis = await get_redis()
    key = f"lock:segment:{segment_id}:slot:{slot_id}"
    token = str(uuid.uuid4())

    acquired = await redis.set(key, token, nx=True, px=LOCK_TIMEOUT_MS)
    if not acquired:
        raise LockAcquisitionError(f"Could not acquire lock for segment {segment_id} slot {slot_id}")

    try:
        yield
    finally:
        stored = await redis.get(key)
        if stored == token:
            await redis.delete(key)
