import time
from fastapi import Request, HTTPException
import redis.asyncio as aioredis
from shared.config import get_settings

settings = get_settings()

RATE_LIMIT = 100       # requests
WINDOW_SECONDS = 60    # per minute


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    try:
        r = aioredis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
        key = f"rate_limit:{client_ip}"
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, WINDOW_SECONDS)
        await r.aclose()
        if current > RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        pass  # fail open — don't block if Redis is down
    return await call_next(request)
