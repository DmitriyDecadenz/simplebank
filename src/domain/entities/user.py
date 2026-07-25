from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash


@dataclass(slots=True, eq=False)
class User:
    """A person who can own bank accounts.

    Identity is defined solely by :attr:`id`; two users are equal when their
    ids match regardless of their current attribute values.
    """

    id: UUID
    email: Email
    password_hash: PasswordHash

    def change_email(self, new_email: Email) -> None:
        self.email = new_email

    def change_password(self, new_password_hash: PasswordHash) -> None:
        self.password_hash = new_password_hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
