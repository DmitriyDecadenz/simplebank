"""Unit tests for the TransferMoney use case (transfer, fee, insufficient funds).

The critical section runs through ``TransactionManager.run``; here it is backed
by an in-memory locking context (see ``FakeTransactionManager``).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from application.dto import TransferMoneyCommand
from application.exceptions import AccountNotFoundError, SameAccountTransferError
from application.usecases.transfer_money import TransferMoney
from conftest import make_account
from domain.enums.transaction_type import TransactionType
from domain.exceptions import InsufficientFundsError


@pytest.fixture
def use_case(transaction_manager):
    return TransferMoney(transaction_manager)


def _setup(tm, *, sender_balance="10000"):
    sender = make_account(number="1111111111", balance=sender_balance)
    recipient = make_account(number="2222222222", balance="0")
    tm.preload_account(sender)
    tm.preload_account(recipient)
    return sender, recipient


async def test_transfer_moves_amount_and_charges_percentage_fee(
    use_case, transaction_manager
):
    sender, recipient = _setup(transaction_manager)

    dto = await use_case.execute(
        TransferMoneyCommand(
            from_account_id=sender.id,
            to_account_number="2222222222",
            amount=Decimal("1000"),
        )
    )

    # Fee = max(1000 * 2.5%, 5) = 25; sender pays amount + fee.
    assert dto.fee == Decimal("25.00")
    assert dto.total_debited == Decimal("1025.00")
    assert dto.amount == Decimal("1000.00")
    assert dto.from_balance == Decimal("8975.00")
    assert dto.to_balance == Decimal("1000.00")

    # One DEBIT (amount + fee) and one CREDIT (amount) recorded.
    assert len(transaction_manager.added_transactions) == 2
    debit = next(
        t for t in transaction_manager.added_transactions if t.type is TransactionType.DEBIT
    )
    credit = next(
        t for t in transaction_manager.added_transactions if t.type is TransactionType.CREDIT
    )
    assert debit.amount.amount == Decimal("1025.00")
    assert credit.amount.amount == Decimal("1000.00")

    # Both balances saved inside a committed transaction.
    assert len(transaction_manager.saved_accounts) == 2
    assert transaction_manager.entered and transaction_manager.committed


@pytest.mark.parametrize(
    ("amount", "expected_fee"),
    [
        ("1000", "25.00"),  # 2.5% dominates
        ("200", "5.00"),  # 2.5% == 5, boundary
        ("100", "5.00"),  # flat minimum dominates
        ("40", "5.00"),  # tiny transfer still pays €5
    ],
)
async def test_transfer_fee_policy(use_case, transaction_manager, amount, expected_fee):
    sender, _ = _setup(transaction_manager)

    dto = await use_case.execute(
        TransferMoneyCommand(
            from_account_id=sender.id,
            to_account_number="2222222222",
            amount=Decimal(amount),
        )
    )

    assert dto.fee == Decimal(expected_fee)
    assert dto.total_debited == (Decimal(amount) + Decimal(expected_fee)).quantize(
        Decimal("0.01")
    )


async def test_transfer_rejects_insufficient_funds_atomically(
    use_case, transaction_manager
):
    # Balance can't cover amount + fee (100 + 5 = 105 > 100).
    sender, recipient = _setup(transaction_manager, sender_balance="100")
    before_sender = sender.balance
    before_recipient = recipient.balance

    with pytest.raises(InsufficientFundsError):
        await use_case.execute(
            TransferMoneyCommand(
                from_account_id=sender.id,
                to_account_number="2222222222",
                amount=Decimal("100"),
            )
        )

    # Nothing persisted, no commit, balances untouched.
    assert transaction_manager.added_transactions == []
    assert transaction_manager.saved_accounts == []
    assert transaction_manager.committed is False
    assert sender.balance == before_sender
    assert recipient.balance == before_recipient


async def test_transfer_unknown_sender(use_case, transaction_manager):
    _setup(transaction_manager)
    from uuid import uuid4

    with pytest.raises(AccountNotFoundError):
        await use_case.execute(
            TransferMoneyCommand(
                from_account_id=uuid4(),
                to_account_number="2222222222",
                amount=Decimal("10"),
            )
        )


async def test_transfer_unknown_recipient(use_case, transaction_manager):
    sender, _ = _setup(transaction_manager)

    with pytest.raises(AccountNotFoundError):
        await use_case.execute(
            TransferMoneyCommand(
                from_account_id=sender.id,
                to_account_number="9999999999",
                amount=Decimal("10"),
            )
        )


async def test_transfer_to_same_account_rejected(use_case, transaction_manager):
    sender, _ = _setup(transaction_manager)

    with pytest.raises(SameAccountTransferError):
        await use_case.execute(
            TransferMoneyCommand(
                from_account_id=sender.id,
                to_account_number="1111111111",
                amount=Decimal("10"),
            )
        )
