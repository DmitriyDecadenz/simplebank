"""Transfer domain service.

Encapsulates the money movement of a transfer between two accounts: it computes
the fee, debits ``amount + fee`` from the sender and credits ``amount`` to the
recipient, returning the resulting ledger entries. Pure and framework-agnostic;
callers are responsible for loading, locking and persisting the accounts.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.services.transfer_fee import calculate_transfer_fee
from domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class TransferEntries:
    """Ledger entries produced by a transfer."""

    debit: Transaction
    credit: Transaction
    fee: Money
    total: Money


def make_transfer(sender: Account, recipient: Account, amount: Money) -> TransferEntries:
    """Apply a transfer of ``amount`` from ``sender`` to ``recipient``.

    Mutates both aggregates' balances and returns the DEBIT/CREDIT entries. The
    sender's ``withdraw`` enforces sufficient funds (``amount + fee``).
    """
    fee = calculate_transfer_fee(amount)
    total = amount.add(fee)
    debit = sender.withdraw(total)
    credit = recipient.deposit(amount)
    return TransferEntries(debit=debit, credit=credit, fee=fee, total=total)
