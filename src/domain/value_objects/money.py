from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from domain.exceptions import (
    CurrencyMismatchError,
    InvalidMoneyError,
    NegativeMoneyError,
)

_CENTS = Decimal("0.01")
_DEFAULT_CURRENCY = "USD"


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable monetary amount.

    Uses :class:`decimal.Decimal` to avoid floating-point rounding errors and
    keeps a currency so amounts of different currencies can never be mixed by
    accident. Amounts are non-negative and quantized to two decimal places.
    """

    amount: Decimal
    currency: str = _DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        try:
            amount = Decimal(self.amount)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise InvalidMoneyError(f"Invalid monetary amount: {self.amount!r}") from exc

        if not amount.is_finite():
            raise InvalidMoneyError(f"Monetary amount must be finite: {self.amount!r}")

        if amount < 0:
            raise NegativeMoneyError(f"Monetary amount must not be negative: {amount}")

        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise InvalidMoneyError(f"Invalid currency code: {self.currency!r}")

        object.__setattr__(self, "amount", amount.quantize(_CENTS, rounding=ROUND_HALF_UP))
        object.__setattr__(self, "currency", currency)

    @classmethod
    def zero(cls, currency: str = _DEFAULT_CURRENCY) -> "Money":
        return cls(Decimal("0"), currency)

    @property
    def is_zero(self) -> bool:
        return self.amount == 0

    def _ensure_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot operate on {self.currency} and {other.currency}"
            )

    def add(self, other: "Money") -> "Money":
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._ensure_same_currency(other)
        # Money is non-negative by invariant; a negative result raises.
        return Money(self.amount - other.amount, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
