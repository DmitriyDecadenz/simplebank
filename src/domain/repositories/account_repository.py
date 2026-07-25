from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from domain.entities.account import Account
from domain.value_objects.account_number import AccountNumber


class AccountRepository(ABC):
    """Persistence abstraction for the :class:`Account` aggregate.

    Implementations live in the infrastructure layer and are accessed through
    the :class:`UnitOfWork` so they share its transaction.
    """

    @abstractmethod
    async def add(self, account: Account) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, account: Account) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, account_id: UUID) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_number(self, account_number: AccountNumber) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_owner(self, owner_id: UUID) -> Sequence[Account]:
        raise NotImplementedError
