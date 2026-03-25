import sys
sys.path.insert(0, "/app")

import asyncio
from fastapi import FastAPI
from shared.health import create_health_router
from shared.database import init_db, Base, get_engine
from routes import router
from consumer import start_consumer
import models  # noqa: F401

app = FastAPI(title="Analytics Service", version="1.0.0")

app.include_router(create_health_router("analytics_service"))
app.include_router(router, prefix="/analytics")


@app.on_event("startup")
async def startup():
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(start_consumer())
