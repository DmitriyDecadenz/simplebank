"""Shared fixtures and test doubles for the use-case unit tests.

Everything the use cases touch (repositories, the transaction manager, the
password hasher and the token service) is faked here, so the tests exercise the
application logic in isolation - no database, no Django, no crypto.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import AsyncIterator, Sequence
from uuid import UUID, uuid4

import pytest

from application.transaction import TransactionManager
from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.entities.user import User
from domain.repositories.account_repository import AccountRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.email import Email
from domain.value_objects.money import Money
from domain.value_objects.password_hash import PasswordHash


class FakeAtomicContext:
    """In-memory stand-in for the locking transactional context."""

    def __init__(self, manager: "FakeTransactionManager") -> None:
        self._m = manager

    def find_account_id_by_number(self, account_number) -> UUID | None:
        account = self._m.accounts_by_number.get(str(account_number))
        return account.id if account else None

    def get_account_for_update(self, account_id: UUID):
        return self._m.accounts_by_id.get(account_id)

    def save_account(self, account) -> None:
        self._m.saved_accounts.append(account)

    def add_transaction(self, transaction) -> None:
        self._m.added_transactions.append(transaction)


class FakeTransactionManager(TransactionManager):
    """Records how the atomic boundaries are used.

    ``committed`` flips to ``True`` only when the ``atomic()`` block or the
    ``run()`` unit of work completes cleanly; if the body raises, it stays
    ``False`` - mirroring the "no partial commits" guarantee.
    """

    def __init__(self) -> None:
        self.entered = False
        self.committed = False
        self.accounts_by_id: dict[UUID, Account] = {}
        self.accounts_by_number: dict[str, Account] = {}
        self.saved_accounts: list[Account] = []
        self.added_transactions: list[Transaction] = []

    def preload_account(self, account: Account) -> None:
        self.accounts_by_id[account.id] = account
        self.accounts_by_number[str(account.account_number)] = account

    @asynccontextmanager
    async def atomic(self) -> AsyncIterator[None]:
        self.entered = True
        yield
        self.committed = True

    async def run(self, work):
        self.entered = True
        result = work(FakeAtomicContext(self))
        self.committed = True
        return result


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.saved: list[User] = []
        self._by_email: dict[str, User] = {}
        self._by_id: dict[UUID, User] = {}

    def preload(self, user: User) -> None:
        self._by_email[str(user.email)] = user
        self._by_id[user.id] = user

    async def add(self, user: User) -> None:
        self.saved.append(user)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        return self._by_email.get(str(email))

    async def exists_by_email(self, email: Email) -> bool:
        return str(email) in self._by_email


class InMemoryAccountRepository(AccountRepository):
    def __init__(self) -> None:
        self.added: list[Account] = []
        self.updated: list[Account] = []
        self._by_id: dict[UUID, Account] = {}
        self._by_number: dict[str, Account] = {}

    def preload(self, account: Account) -> None:
        self._by_id[account.id] = account
        self._by_number[str(account.account_number)] = account

    async def add(self, account: Account) -> None:
        self.added.append(account)

    async def update(self, account: Account) -> None:
        self.updated.append(account)

    async def get_by_id(self, account_id: UUID) -> Account | None:
        return self._by_id.get(account_id)

    async def get_by_number(self, account_number: AccountNumber) -> Account | None:
        return self._by_number.get(str(account_number))

    async def list_by_owner(self, owner_id: UUID) -> Sequence[Account]:
        return [a for a in self._by_id.values() if a.owner_id == owner_id]


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self) -> None:
        self.added: list[Transaction] = []

    async def add(self, transaction: Transaction) -> None:
        self.added.append(transaction)

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return next((t for t in self.added if t.id == transaction_id), None)

    async def list_by_account(self, account_id: UUID) -> Sequence[Transaction]:
        return [t for t in self.added if t.account_id == account_id]


class StubPasswordHasher:
    """Deterministic, reversible-enough stand-in for a real hasher."""

    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{password}"


class StubTokenService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def create_access_token(self, subject: str, claims: dict | None = None) -> str:
        self.calls.append((subject, dict(claims or {})))
        return f"token-for-{subject}"

    def decode(self, token: str) -> dict:
        return {"sub": token.removeprefix("token-for-")}


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def accounts() -> InMemoryAccountRepository:
    return InMemoryAccountRepository()


@pytest.fixture
def transactions() -> InMemoryTransactionRepository:
    return InMemoryTransactionRepository()


@pytest.fixture
def transaction_manager() -> FakeTransactionManager:
    return FakeTransactionManager()


@pytest.fixture
def password_hasher() -> StubPasswordHasher:
    return StubPasswordHasher()


@pytest.fixture
def token_service() -> StubTokenService:
    return StubTokenService()


def make_user(email: str = "user@example.com", password: str = "secret") -> User:
    return User(
        id=uuid4(),
        email=Email(email),
        password_hash=PasswordHash(f"hashed::{password}"),
    )


def make_account(
    *,
    owner_id: UUID | None = None,
    number: str = "1234567890",
    balance: str = "10000",
    currency: str = "EUR",
) -> Account:
    return Account(
        id=uuid4(),
        owner_id=owner_id or uuid4(),
        account_number=AccountNumber(number),
        balance=Money(Decimal(balance), currency),
    )


def make_transaction(
    account_id: UUID,
    *,
    amount: str = "100",
    type_: str = "CREDIT",
    currency: str = "EUR",
) -> Transaction:
    from domain.enums.transaction_type import TransactionType

    return Transaction(
        id=uuid4(),
        account_id=account_id,
        amount=Money(Decimal(amount), currency),
        type=TransactionType(type_),
        created_at=datetime.now(UTC),
    )
