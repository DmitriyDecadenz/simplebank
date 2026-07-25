from __future__ import annotations

import re
from dataclasses import dataclass

from domain.exceptions import InvalidAccountNumberError

# 10 to 20 digits, a pragmatic superset that covers most domestic schemes.
_ACCOUNT_NUMBER_PATTERN = re.compile(r"^\d{10,20}$")


@dataclass(frozen=True, slots=True)
class AccountNumber:
    """Bank account number value object.

    Enforces a digits-only format of a fixed length range. Any spaces are
    stripped before validation so callers may pass user-formatted input.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.replace(" ", "").strip()
        if not _ACCOUNT_NUMBER_PATTERN.match(normalized):
            raise InvalidAccountNumberError(
                f"Invalid account number: {self.value!r}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
