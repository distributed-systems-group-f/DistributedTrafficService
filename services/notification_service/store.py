import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session_factory
from models import Notification


async def persist_notification(
    user_id: str,
    booking_id: str | None,
    event_type: str,
    channel: str,
    message: str,
) -> None:
    factory = get_session_factory()
    async with factory() as db:
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            booking_id=booking_id,
            event_type=event_type,
            channel=channel,
            message=message,
        )
        db.add(notification)
        await db.commit()


async def list_notifications(db: AsyncSession, user_id: str, limit: int = 20) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.sent_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
