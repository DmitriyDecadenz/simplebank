"""Unit of Work abstraction.

The Unit of Work owns the transactional boundary and exposes the repositories
that participate in that transaction. The application layer depends on this
abstraction only; the SQLAlchemy implementation lives in the infrastructure
layer (Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from domain.repositories.account_repository import AccountRepository
from domain.repositories.outbox_repository import OutboxRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository


class AbstractUnitOfWork(ABC):
    """Transactional boundary exposing the repositories it manages.

    Usage::

        async with uow:
            account = await uow.accounts.get_by_id(account_id)
            transaction = account.deposit(amount)
            await uow.transactions.add(transaction)
            await uow.accounts.update(account)
            await uow.commit()

    Leaving the context manager without an explicit :meth:`commit` rolls the
    transaction back, guaranteeing atomicity.
    """

    users: UserRepository
    accounts: AccountRepository
    transactions: TransactionRepository
    outbox: OutboxRepository

    async def __aenter__(self) -> Self:
        """Enter the transactional context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back automatically unless the work was explicitly committed."""
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        """Persist all changes accumulated within the current transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all changes accumulated within the current transaction."""
        raise NotImplementedError
