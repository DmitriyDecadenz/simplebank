"""SQLAlchemy read-side (query) implementations.

These bypass the ORM entity hydration and the Unit of Work: each query opens a
short-lived read session and selects only the columns it needs, returning a
projection DTO. This is the read half of CQRS.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.dto import BalanceDTO
from application.queries.get_balance import AccountBalanceReader
from infrastructure.database.sqlalchemy.models import AccountModel


class SqlAlchemyAccountBalanceReader(AccountBalanceReader):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_balance(self, account_id: UUID) -> BalanceDTO | None:
        stmt = select(
            AccountModel.account_number,
            AccountModel.balance,
            AccountModel.currency,
        ).where(AccountModel.id == account_id)

        async with self._session_factory() as session:
            row = (await session.execute(stmt)).one_or_none()

        if row is None:
            return None
        return BalanceDTO(
            account_number=row.account_number,
            balance=row.balance,
            currency=row.currency,
        )
