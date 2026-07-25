from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    """Persistence abstraction for the :class:`Transaction` entity.

    Transactions are an immutable ledger, hence only append/read operations are
    exposed. Writes participate in the surrounding ``TransactionManager.atomic()``
    block when one is active.
    """

    @abstractmethod
    async def add(self, transaction: Transaction) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_account(self, account_id: UUID) -> Sequence[Transaction]:
        raise NotImplementedError
