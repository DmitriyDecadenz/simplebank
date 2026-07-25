from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.enums.transaction_type import TransactionType
from domain.exceptions import InvalidAmountError
from domain.value_objects.money import Money


@dataclass(slots=True, eq=False)
class Transaction:
    """An immutable record of a single money movement on an account.

    A transaction is created by the owning :class:`Account` when funds are
    deposited or withdrawn. The ``amount`` is always a strictly positive
    :class:`Money`; the direction is carried by :attr:`type`.
    """

    id: UUID
    account_id: UUID
    amount: Money
    type: TransactionType
    created_at: datetime

    def __post_init__(self) -> None:
        if self.amount.is_zero:
            raise InvalidAmountError("Transaction amount must be strictly positive")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
