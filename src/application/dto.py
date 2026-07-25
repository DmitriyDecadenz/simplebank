"""Data Transfer Objects exchanged with the outer layers.

DTOs are plain, framework-agnostic data carriers. They deliberately expose
primitives (``str``/``Decimal``/``UUID``) instead of domain value objects so the
presentation layer never depends on the domain internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    """Input for the RegisterUser use case."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Input for the Login use case."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class TokenDTO:
    """Output of the Login use case: an OAuth2-style bearer token."""

    access_token: str
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class AccountDTO:
    id: UUID
    account_number: str
    balance: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class BalanceDTO:
    """Read-side projection returned by the GetBalance query."""

    account_number: str
    balance: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class UserDTO:
    """Output of the RegisterUser use case.

    Includes the account that is automatically opened on registration together
    with its welcome-bonus balance.
    """

    id: UUID
    email: str
    account: AccountDTO
