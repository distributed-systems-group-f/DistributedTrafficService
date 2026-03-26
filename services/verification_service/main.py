import sys
import asyncio
import logging
sys.path.insert(0, "/app")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from shared.health import create_health_router
from shared.redis_client import close_redis
from routes import router
from consumer import start_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: launch background RabbitMQ consumer that keeps the Redis
    cache warm whenever the booking service confirms / cancels a journey.
    On shutdown: cancel the consumer and release the Redis connection.
    """
    global _consumer_task
    try:
        _consumer_task = asyncio.create_task(start_consumer())
        logger.info("Verification service started — cache-warming consumer running")
    except Exception as e:
        # Non-fatal in local dev when RabbitMQ may not be up yet
        logger.warning(f"Consumer failed to start (non-fatal in dev): {e}")
    yield
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    await close_redis()
    logger.info("Verification service shut down cleanly")


app = FastAPI(
    title="Verification Service",
    version="1.0.0",
    description=(
        "Enforcement agent lookup. Returns active booking status for a plate "
        "number in <100 ms via Redis-first, Aurora read-replica fallback."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_health_router("verification_service"))
app.include_router(router, prefix="/verify")