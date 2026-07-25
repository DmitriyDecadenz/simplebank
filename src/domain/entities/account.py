from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.entities.transaction import Transaction
from domain.enums.transaction_type import TransactionType
from domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    NegativeBalanceError,
)
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.money import Money


@dataclass(slots=True, eq=False)
class Account:
    """A bank account owned by a user.

    The account is the aggregate root guarding its own balance: money can only
    move through :meth:`deposit` and :meth:`withdraw`, both of which keep the
    ``balance >= 0`` invariant and emit a :class:`Transaction` describing the
    change.
    """

    id: UUID
    owner_id: UUID
    account_number: AccountNumber
    balance: Money

    def deposit(self, amount: Money) -> Transaction:
        """Add ``amount`` to the balance and record a CREDIT transaction."""
        self._ensure_positive(amount)
        self.balance = self.balance.add(amount)
        return self._record(amount, TransactionType.CREDIT)

    def withdraw(self, amount: Money) -> Transaction:
        """Remove ``amount`` from the balance and record a DEBIT transaction."""
        self._ensure_positive(amount)
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Cannot withdraw {amount}: available balance is {self.balance}"
            )
        self.balance = self.balance.subtract(amount)
        return self._record(amount, TransactionType.DEBIT)

    def validate_balance(self) -> None:
        """Assert the account invariant that the balance is never negative.

        :class:`Money` already forbids negative amounts, so this acts as an
        explicit, self-documenting guard for the aggregate invariant.
        """
        if self.balance.amount < 0:
            raise NegativeBalanceError(
                f"Account {self.id} has a negative balance: {self.balance}"
            )

    def _ensure_positive(self, amount: Money) -> None:
        if amount.currency != self.balance.currency:
            raise InvalidAmountError(
                f"Amount currency {amount.currency} does not match "
                f"account currency {self.balance.currency}"
            )
        if amount.is_zero:
            raise InvalidAmountError("Amount must be strictly positive")

    def _record(self, amount: Money, type_: TransactionType) -> Transaction:
        return Transaction(
            id=uuid4(),
            account_id=self.id,
            amount=amount,
            type=type_,
            created_at=datetime.now(UTC),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
