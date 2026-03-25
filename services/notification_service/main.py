import sys
sys.path.insert(0, "/app")

import asyncio
from fastapi import FastAPI
from shared.health import create_health_router
from routes import router
from consumer import start_consumer

app = FastAPI(title="Notification Service", version="1.0.0")

app.include_router(create_health_router("notification_service"))
app.include_router(router, prefix="/notifications")


@app.on_event("startup")
async def startup():
    asyncio.create_task(start_consumer())
