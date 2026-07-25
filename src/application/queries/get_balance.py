"""GetBalance query (CQRS read side).

The read side is fully separated from the command side: it does not go through
the domain aggregates or the write repositories. Instead it depends on a thin
read port that returns a projection DTO directly, keeping queries free of any
business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.dto import BalanceDTO
from application.exceptions import AccountNotFoundError


@dataclass(frozen=True, slots=True)
class GetBalanceQuery:
    """Input for the GetBalance query."""

    account_id: UUID


class AccountBalanceReader(ABC):
    """Read port returning a balance projection, bypassing the domain model."""

    @abstractmethod
    async def get_balance(self, account_id: UUID) -> BalanceDTO | None:
        raise NotImplementedError


class GetBalance:
    """Return the account number and balance for an account."""

    def __init__(self, reader: AccountBalanceReader) -> None:
        self._reader = reader

    async def execute(self, query: GetBalanceQuery) -> BalanceDTO:
        balance = await self._reader.get_balance(query.account_id)
        if balance is None:
            raise AccountNotFoundError(f"Account not found: {query.account_id}")
        return balance
