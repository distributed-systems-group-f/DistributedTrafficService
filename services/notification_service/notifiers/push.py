import logging
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class PushNotifier(BaseNotifier):
    """Firebase FCM stub."""

    async def send(self, user_id: str, message: str) -> bool:
        logger.info(f"[PUSH] To {user_id}: {message}")
        return True
