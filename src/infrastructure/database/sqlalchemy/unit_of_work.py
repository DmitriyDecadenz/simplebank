"""SQLAlchemy implementation of the Unit of Work."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.unit_of_work import AbstractUnitOfWork
from src.infrastructure.db.sqlalchemy.repositories import (
    SqlAlchemyValidationRuleRepository,
    SqlAlchemyValidationHistoryRepository,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unit of Work backed by a SQLAlchemy ``AsyncSession``.

    A new session is opened on ``__aenter__`` and closed on ``__aexit__``. The
    repositories created within share that single session, so all of their work
    participates in one atomic transaction.
    """

    validation_rule: SqlAlchemyValidationRuleRepository
    validation_history: SqlAlchemyValidationHistoryRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialise the UoW with a session factory.

        Args:
            session_factory: Factory producing fresh async sessions per scope.
        """
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        """Open a session and wire up the repositories for this scope."""
        self._session = self._session_factory()
        # init your repositories
        # self.your_repository = SqlAlchemyYourRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back any pending work and close the session."""
        try:
            await self.rollback()
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is None:
            raise RuntimeError(
                "Unit of Work is not active; use it as a context manager"
            )
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction (no-op if nothing is pending)."""
        if self._session is not None:
            await self._session.rollback()
