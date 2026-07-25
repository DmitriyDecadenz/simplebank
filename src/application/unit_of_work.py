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

from src.domain.repositories.validation_history_repository import (
    ValidationHistoryRepository,
)
from src.domain.repositories.validation_rule_repository import ValidationRuleRepository


class AbstractUnitOfWork(ABC):
    """Transactional boundary exposing the repositories it manages.

    Usage::

        async with uow:
            await uow.validation_rule.add(aggregate)
            await uow.commit()

    Leaving the context manager without an explicit :meth:`commit` rolls the
    transaction back, guaranteeing atomicity.
    """

    validation_rule: ValidationRuleRepository
    validation_history: ValidationHistoryRepository

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
