import logging
import uuid
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.auth import create_access_token
from shared.exceptions import AuthenticationError, UserNotFoundError
from shared.messaging import publish_event
from shared.redis_client import get_redis
from models import User, ReplicatedUser

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_LOCK_TTL = 86400  # 24 hours — permanent claim on email


async def register_user(db: AsyncSession, email: str, password: str, role: str, **kwargs) -> User:
    # Global distributed lock on email — prevents duplicate registration across VMs
    redis = await get_redis()
    email_key = f"email:registered:{email.lower()}"
    claimed = await redis.set(email_key, "1", nx=True, ex=EMAIL_LOCK_TTL)
    if not claimed:
        raise ValueError(f"Email {email} is already registered.")

    # Also check replica — belt and suspenders
    replica_result = await db.execute(select(ReplicatedUser).where(ReplicatedUser.email == email))
    if replica_result.scalar_one_or_none():
        raise ValueError(f"Email {email} is already registered on another regional node.")

    hashed = pwd_context.hash(password.encode("utf-8")[:72].decode("utf-8", errors="ignore"))
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=hashed,
        role=role,
        **kwargs,
    )
    db.add(user)

    replication_payload = {
        "event_type": "user.registered",
        "user_id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "role": user.role,
        "plate_number": user.plate_number,
        "region": user.region,
        "created_at": user.created_at.isoformat(),
    }

    # Publish BEFORE commit — if commit fails, send compensating rollback event
    await publish_event(routing_key="user.registered", payload=replication_payload)
    logger.info(f"[REPLICATION] Published user.registered for user={user.id[:8]} email={user.email}")

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        logger.error(f"[REPLICATION] DB commit failed for {user.email}: {e} — sending compensating rollback")
        await db.rollback()
        # Release email lock so user can retry
        await redis.delete(email_key)
        # Compensating transaction — tell peer VM to undo the replication
        try:
            await publish_event(
                routing_key="user.registration_failed",
                payload={"event_type": "user.registration_failed", "user_id": user.id, "email": user.email},
            )
        except Exception as pub_err:
            logger.error(f"[REPLICATION] Failed to publish rollback event: {pub_err}")
        raise

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> tuple[User | ReplicatedUser, str]:
    password_encoded = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    # Check local users first
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Fall back to replicated users (eventual consistency from peer VM)
        result = await db.execute(select(ReplicatedUser).where(ReplicatedUser.email == email))
        user = result.scalar_one_or_none()
        if user:
            logger.info(f"[REPLICATION] Login via replicated user email={email} — peer VM user")

    if not user or not pwd_context.verify(password_encoded, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    token = create_access_token(subject=user.id, role=user.role, extra={"email": user.email})
    return user, token


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | ReplicatedUser:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        result = await db.execute(select(ReplicatedUser).where(ReplicatedUser.id == user_id))
        user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user