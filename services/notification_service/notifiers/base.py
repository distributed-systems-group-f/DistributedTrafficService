from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    @abstractmethod
    async def send(self, user_id: str, message: str) -> bool:
        pass
