import logging
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class SMSNotifier(BaseNotifier):
    """Twilio SMS stub."""

    async def send(self, user_id: str, message: str) -> bool:
        logger.info(f"[SMS] To {user_id}: {message}")
        return True
