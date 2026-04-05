from fastapi import Request, HTTPException
import redis.asyncio as aioredis
from shared.config import get_settings

settings = get_settings()

RATE_LIMIT = 100       # requests
WINDOW_SECONDS = 60    # per minute

_redis_client: aioredis.Redis | None = None


async def _get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
    return _redis_client


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    try:
        r = await _get_redis_client()
        key = f"rate_limit:{client_ip}"
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, WINDOW_SECONDS)
        if current > RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        pass  # fail open — don't block if Redis is down
    return await call_next(request)
