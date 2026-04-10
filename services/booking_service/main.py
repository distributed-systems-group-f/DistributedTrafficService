import sys
sys.path.insert(0, "/app")

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
from shared.health import create_health_router
from shared.database import init_db, Base, get_engine
from routes import router
from reconciler import reconciliation_loop, run_reconciliation_once
import models  # noqa: F401

logger = logging.getLogger(__name__)

_reconciler_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _reconciler_task
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start the reconciler background loop (crash recovery + partition healing)
    _reconciler_task = asyncio.create_task(reconciliation_loop())
    logger.info("Saga reconciler started")
    yield

    if _reconciler_task:
        _reconciler_task.cancel()
        try:
            await _reconciler_task
        except asyncio.CancelledError:
            pass
    logger.info("Booking service shut down cleanly")


app = FastAPI(title="Booking Service", version="1.0.0", redirect_slashes=False, lifespan=lifespan)

app.include_router(create_health_router("booking_service"))
app.include_router(router, prefix="/bookings")