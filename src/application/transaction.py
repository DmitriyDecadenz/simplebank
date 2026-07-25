"""Transaction boundary abstraction.

Replaces the Unit of Work: repositories are injected into use cases directly,
and multi-step writes are made atomic by wrapping them in ``async with
transaction_manager.atomic():``. The concrete transactional behaviour lives in
the infrastructure layer (Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager


class TransactionManager(ABC):
    """Provides an atomic boundary for a group of repository writes.

    Usage::

        async with transaction_manager.atomic():
            await users.add(user)
            await accounts.add(account)

    On success every write performed inside the block is committed together; if
    the block raises, none of them are persisted.
    """

    @abstractmethod
    def atomic(self) -> AbstractAsyncContextManager[None]:
        raise NotImplementedError
