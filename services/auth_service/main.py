import sys
sys.path.insert(0, "/app")

from fastapi import FastAPI
from sqlalchemy import text
from shared.health import create_health_router
from shared.database import init_db, Base, get_engine
from routes import router
import models  # noqa: F401 — registers ORM models

app = FastAPI(redirect_slashes=False, title="Auth Service", version="1.0.0")

app.include_router(create_health_router("auth_service"))
app.include_router(router, prefix="/auth")


@app.on_event("startup")
async def startup():
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await conn.run_sync(Base.metadata.create_all)