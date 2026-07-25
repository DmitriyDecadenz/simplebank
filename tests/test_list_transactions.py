"""Unit tests for the ListTransactions query."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from application.dto import TransactionListItemDTO
from application.queries.list_transactions import (
    ListTransactions,
    ListTransactionsQuery,
    TransactionHistoryReader,
)


class RecordingHistoryReader(TransactionHistoryReader):
    def __init__(self, items):
        self._items = items
        self.received: dict | None = None

    async def list_transactions(self, account_id, date_from=None, date_to=None):
        self.received = {
            "account_id": account_id,
            "date_from": date_from,
            "date_to": date_to,
        }
        return self._items


def _item(amount: str, type_: str, when: datetime) -> TransactionListItemDTO:
    return TransactionListItemDTO(
        amount=Decimal(amount), currency="EUR", type=type_, created_at=when
    )


async def test_list_transactions_returns_reader_items():
    account_id = uuid4()
    items = [
        _item("100.00", "CREDIT", datetime(2026, 1, 2, tzinfo=UTC)),
        _item("50.00", "DEBIT", datetime(2026, 1, 1, tzinfo=UTC)),
    ]
    reader = RecordingHistoryReader(items)

    result = await ListTransactions(reader).execute(
        ListTransactionsQuery(account_id=account_id)
    )

    assert list(result) == items


async def test_list_transactions_passes_date_filters_to_reader():
    account_id = uuid4()
    date_from = datetime(2026, 1, 1, tzinfo=UTC)
    date_to = datetime(2026, 1, 31, tzinfo=UTC)
    reader = RecordingHistoryReader([])

    await ListTransactions(reader).execute(
        ListTransactionsQuery(
            account_id=account_id, date_from=date_from, date_to=date_to
        )
    )

    assert reader.received == {
        "account_id": account_id,
        "date_from": date_from,
        "date_to": date_to,
    }
