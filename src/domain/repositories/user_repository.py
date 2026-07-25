from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.user import User
from domain.value_objects.email import Email


class UserRepository(ABC):
    """Persistence abstraction for the :class:`User` aggregate.

    Implementations live in the infrastructure layer. Writes performed inside a
    ``TransactionManager.atomic()`` block are committed together.
    """

    @abstractmethod
    async def add(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        raise NotImplementedError
