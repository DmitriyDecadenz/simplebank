from __future__ import annotations

import re
from dataclasses import dataclass

from domain.exceptions import InvalidEmailError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    """Email address value object.

    Guarantees a syntactically valid, normalized (lower-cased, trimmed) value.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"Invalid email address: {self.value!r}")
        # frozen dataclass: bypass immutability to store the normalized form.
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
