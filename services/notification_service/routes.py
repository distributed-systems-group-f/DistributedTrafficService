from fastapi import APIRouter, Depends
from shared.auth import get_current_user
from datetime import datetime

router = APIRouter()


@router.get("/{user_id}")
async def get_notifications(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    # In production this would query a notifications store
    return {"user_id": user_id, "notifications": [], "message": "No notifications yet"}
