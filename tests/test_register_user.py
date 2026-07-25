"""Unit tests for the RegisterUser use case."""

from __future__ import annotations

from decimal import Decimal

import pytest

from application.dto import RegisterUserCommand
from application.exceptions import EmailAlreadyExistsError
from application.usecases.register_user import RegisterUser
from conftest import make_user
from domain.enums.transaction_type import TransactionType


@pytest.fixture
def use_case(users, accounts, transactions, transaction_manager, password_hasher):
    return RegisterUser(
        users, accounts, transactions, password_hasher, transaction_manager
    )


async def test_register_creates_user_account_and_welcome_bonus(
    use_case, users, accounts, transactions, transaction_manager
):
    dto = await use_case.execute(
        RegisterUserCommand(email="Alice@Example.com", password="s3cret!!")
    )

    # Email is normalised, account is opened with the €10000 welcome bonus.
    assert dto.email == "alice@example.com"
    assert dto.account.balance == Decimal("10000.00")
    assert dto.account.currency == "EUR"
    assert len(dto.account.account_number) == 10 and dto.account.account_number.isdigit()

    # Everything was persisted...
    assert len(users.saved) == 1
    assert len(accounts.added) == 1
    assert len(transactions.added) == 1

    # ...atomically (inside a committed atomic block).
    assert transaction_manager.entered is True
    assert transaction_manager.committed is True

    # The welcome bonus is recorded as a CREDIT transaction.
    bonus = transactions.added[0]
    assert bonus.type is TransactionType.CREDIT
    assert bonus.amount.amount == Decimal("10000.00")


async def test_register_hashes_the_password(use_case, users):
    await use_case.execute(
        RegisterUserCommand(email="bob@example.com", password="hunter2")
    )
    stored = users.saved[0]
    assert str(stored.password_hash) == "hashed::hunter2"


async def test_register_rejects_duplicate_email(use_case, users, transaction_manager):
    users.preload(make_user(email="taken@example.com"))

    with pytest.raises(EmailAlreadyExistsError):
        await use_case.execute(
            RegisterUserCommand(email="taken@example.com", password="whatever")
        )

    # Nothing persisted, atomic block never entered.
    assert users.saved == []
    assert transaction_manager.entered is False
