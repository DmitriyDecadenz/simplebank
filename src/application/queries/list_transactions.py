"""ListTransactions query (CQRS read side).

Returns an account's transaction history, optionally filtered by a date range
and ordered newest-first. Like every query it depends only on a thin read port
and carries no business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from uuid import UUID

from application.dto import TransactionListItemDTO


@dataclass(frozen=True, slots=True)
class ListTransactionsQuery:
    """Input for the ListTransactions query.

    ``date_from``/``date_to`` are optional, inclusive bounds on ``created_at``.
    """

    account_id: UUID
    date_from: datetime | None = None
    date_to: datetime | None = None


class TransactionHistoryReader(ABC):
    """Read port returning a transaction-history projection."""

    @abstractmethod
    async def list_transactions(
        self,
        account_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> Sequence[TransactionListItemDTO]:
        raise NotImplementedError


class ListTransactions:
    """Return an account's transactions, newest first."""

    def __init__(self, reader: TransactionHistoryReader) -> None:
        self._reader = reader

    async def execute(
        self, query: ListTransactionsQuery
    ) -> Sequence[TransactionListItemDTO]:
        return await self._reader.list_transactions(
            account_id=query.account_id,
            date_from=query.date_from,
            date_to=query.date_to,
        )
