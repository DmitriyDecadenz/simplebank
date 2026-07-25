"""Unit tests for the GetBalance query."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from application.dto import BalanceDTO
from application.exceptions import AccountNotFoundError
from application.queries.get_balance import (
    AccountBalanceReader,
    GetBalance,
    GetBalanceQuery,
)


class StubBalanceReader(AccountBalanceReader):
    def __init__(self, balance: BalanceDTO | None) -> None:
        self._balance = balance

    async def get_balance(self, account_id):
        return self._balance


async def test_get_balance_returns_projection():
    account_id = uuid4()
    reader = StubBalanceReader(
        BalanceDTO(account_number="1234567890", balance=Decimal("42.50"), currency="EUR")
    )

    dto = await GetBalance(reader).execute(GetBalanceQuery(account_id=account_id))

    assert dto.account_number == "1234567890"
    assert dto.balance == Decimal("42.50")
    assert dto.currency == "EUR"


async def test_get_balance_raises_when_account_missing():
    reader = StubBalanceReader(None)

    with pytest.raises(AccountNotFoundError):
        await GetBalance(reader).execute(GetBalanceQuery(account_id=uuid4()))
