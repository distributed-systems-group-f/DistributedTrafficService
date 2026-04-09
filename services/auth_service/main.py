import sys
sys.path.insert(0, "/app")

import asyncio
import logging
import logging.config
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped": {
            "format": "%(asctime)s.%(msecs)03d [%(name)s] %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "timestamped",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
})
from sqlalchemy import text, select
from sqlalchemy.dialects.postgresql import insert
from shared.health import create_health_router
from shared.database import init_db, Base, get_engine, get_session_factory
from shared.messaging import consume_replication_events
from routes import router
import models  # noqa: F401 — registers ORM models
from models import ReplicatedUser

logger = logging.getLogger(__name__)
_consumer_task = None


async def handle_user_registered(payload: dict) -> None:
    """Replicate a user from the peer VM into the local auth_replica schema."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            stmt = insert(ReplicatedUser).values(
                id=payload["user_id"],
                email=payload["email"],
                password_hash=payload["password_hash"],
                role=payload.get("role", "driver"),
                plate_number=payload.get("plate_number"),
                region=payload.get("region"),
                created_at=datetime.fromisoformat(payload["created_at"]),
                replicated_at=datetime.utcnow(),
            ).on_conflict_do_nothing()
            await db.execute(stmt)
            await db.commit()
            logger.info(f"[REPLICATION] Replicated user email={payload['email']} from peer VM")
    except Exception as e:
        logger.error(f"[REPLICATION] Failed to replicate user {payload.get('email')}: {e}")


async def handle_user_registration_failed(payload: dict) -> None:
    """Compensating transaction — remove replicated user if peer VM's commit failed."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(ReplicatedUser).where(ReplicatedUser.id == payload["user_id"])
            )
            user = result.scalar_one_or_none()
            if user:
                await db.delete(user)
                await db.commit()
                logger.info(f"[REPLICATION] Compensated — removed replicated user email={payload['email']}")
            else:
                logger.info(f"[REPLICATION] Compensate: user {payload['email']} not in replica, nothing to remove")
    except Exception as e:
        logger.error(f"[REPLICATION] Compensation failed for {payload.get('email')}: {e}")


async def handle_replication_event(payload: dict) -> None:
    """Route replication events to correct handler."""
    event_type = payload.get("event_type")
    if event_type == "user.registered":
        await handle_user_registered(payload)
    elif event_type == "user.registration_failed":
        await handle_user_registration_failed(payload)
    else:
        logger.warning(f"[REPLICATION] Unknown event type: {event_type}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth_replica"))
        await conn.run_sync(Base.metadata.create_all)

    # Start user replication consumer
    _consumer_task = asyncio.create_task(
        consume_replication_events(
            queue_name="auth.user_replication",
            routing_keys=["user.registered", "user.registration_failed"],
            handler=handle_replication_event,
        )
    )
    logger.info("[REPLICATION] User replication consumer started")
    yield

    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(redirect_slashes=False, title="Auth Service", version="1.0.0", lifespan=lifespan)

app.include_router(create_health_router("auth_service"))
app.include_router(router, prefix="/auth")