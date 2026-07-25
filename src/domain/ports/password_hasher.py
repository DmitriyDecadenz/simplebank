from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PasswordHasher(Protocol):
    """Port for hashing and verifying passwords.

    Hashing is an infrastructure concern (algorithm choice, work factor), so the
    application depends only on this abstraction. The domain never sees plaintext
    passwords beyond the moment they are hashed.
    """

    def hash(self, plain_password: str) -> str:
        """Return an opaque, self-describing hash for ``plain_password``."""
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Return ``True`` if ``plain_password`` matches ``hashed_password``."""
        ...
