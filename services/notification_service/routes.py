from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db
from shared.auth import get_current_user
from schemas import NotificationOut
import store

router = APIRouter()


@router.get("/{user_id}", response_model=list[NotificationOut])
async def get_notifications(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
):
    if current_user.get("sub") != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot view another user's notifications")

    notifications = await store.list_notifications(db, user_id, limit)
    return [
        NotificationOut(
            id=n.id,
            user_id=n.user_id,
            message=n.message,
            channel=n.channel,
            sent_at=n.sent_at,
            read=False,
        )
        for n in notifications
    ]
