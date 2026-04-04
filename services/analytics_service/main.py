import sys
sys.path.insert(0, "/app")

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from shared.health import create_health_router
from shared.database import init_db, Base, get_engine
from routes import router
from consumer import start_consumer
import models  # noqa: F401

logger = logging.getLogger(__name__)

_consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        await conn.run_sync(Base.metadata.create_all)

    _consumer_task = asyncio.create_task(start_consumer())
    logger.info("Analytics consumer started")
    yield

    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    logger.info("Analytics service shut down cleanly")


app = FastAPI(
    redirect_slashes=False,
    title="Analytics Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(create_health_router("analytics_service"))
app.include_router(router, prefix="/analytics")