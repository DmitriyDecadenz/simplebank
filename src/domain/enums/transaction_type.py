from __future__ import annotations

from enum import StrEnum


class TransactionType(StrEnum):
    """Direction of a money movement on an account."""

    CREDIT = "CREDIT"  # money added to the account (deposit)
    DEBIT = "DEBIT"  # money removed from the account (withdrawal)
