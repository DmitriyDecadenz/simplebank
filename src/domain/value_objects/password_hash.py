from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import InvalidPasswordHashError


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Wrapper around an already-hashed password.

    The domain never handles plaintext passwords; hashing is an infrastructure
    concern. This value object only guarantees the stored hash is non-empty.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidPasswordHashError("Password hash must not be empty")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        # Avoid leaking the hash in logs/tracebacks.
        return "PasswordHash(***)"
