"""Transaction boundary abstractions.

Two complementary tools replace the Unit of Work:

* :meth:`TransactionManager.atomic` — an async context manager for grouping a
  set of *writes* into one atomic commit (used when no prior read must be locked,
  e.g. registering a user).
* :meth:`TransactionManager.run` — executes a *synchronous* unit of work inside a
  single database transaction and hands it an :class:`AtomicContext`. Reads done
  through that context take row locks (``SELECT ... FOR UPDATE``), so a
  read-modify-write critical section (e.g. a money transfer) is free of races and
  lost updates.

The concrete transactional behaviour lives in the infrastructure layer
(Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Callable, Protocol, TypeVar
from uuid import UUID

from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.value_objects.account_number import AccountNumber

T = TypeVar("T")


class AtomicContext(Protocol):
    """Repository operations bound to a single, open database transaction.

    Account reads acquire row locks that are held until the transaction commits.
    """

    def find_account_id_by_number(self, account_number: AccountNumber) -> UUID | None:
        """Resolve an account id by its (immutable) number, without locking."""
        ...

    def get_account_for_update(self, account_id: UUID) -> Account | None:
        """Load an account and lock its row for the rest of the transaction."""
        ...

    def save_account(self, account: Account) -> None:
        ...

    def add_transaction(self, transaction: Transaction) -> None:
        ...


class TransactionManager(ABC):
    """Provides atomic boundaries for repository operations."""

    @abstractmethod
    def atomic(self) -> AbstractAsyncContextManager[None]:
        """Group buffered writes into one commit (no locking of prior reads)."""
        raise NotImplementedError

    @abstractmethod
    async def run(self, work: Callable[[AtomicContext], T]) -> T:
        """Run ``work`` in one DB transaction with locking reads.

        ``work`` is synchronous, receives an :class:`AtomicContext`, and its
        result is returned. If it raises, the transaction is rolled back.
        """
        raise NotImplementedError
