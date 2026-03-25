import logging
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Email stub."""

    async def send(self, user_id: str, message: str) -> bool:
        logger.info(f"[EMAIL] To {user_id}: {message}")
        return True
