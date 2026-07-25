"""Transfer fee policy.

The fee for a money transfer is ``max(amount * 2.5%, €5)``: a percentage of the
transferred amount, but never less than the flat minimum. Expressed purely with
:class:`Money` so the rule stays framework-agnostic.
"""

from __future__ import annotations

from decimal import Decimal

from domain.value_objects.money import Money

FEE_RATE = Decimal("0.025")
MIN_FEE = Decimal("5")


def calculate_transfer_fee(amount: Money) -> Money:
    """Return the fee charged for transferring ``amount``.

    The flat minimum is applied in the same currency as ``amount``.
    """
    percentage_fee = amount.multiply(FEE_RATE)
    minimum_fee = Money(MIN_FEE, amount.currency)
    return percentage_fee if percentage_fee >= minimum_fee else minimum_fee
