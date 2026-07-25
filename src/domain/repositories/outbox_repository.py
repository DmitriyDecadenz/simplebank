from abc import abstractmethod, ABC
from typing import Sequence
from uuid import UUID

from domain.entities.outbox import OutboxMessage
from domain.event import DomainEvent


class OutboxRepository(ABC):
    @abstractmethod
    async def add(self, event: DomainEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_many(self, events: Sequence[DomainEvent]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_pending(self, limit: int = 100) -> Sequence[OutboxMessage]:
        raise NotImplementedError

    @abstractmethod
    async def mark_published(self, message_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(self, message_id: UUID, error: str) -> None:
        raise NotImplementedError