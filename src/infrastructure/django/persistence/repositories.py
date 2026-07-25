"""Django ORM implementations of the domain repository interfaces.

Reads use the async ORM directly. Writes are delegated to the
:class:`DjangoTransactionManager`, which either buffers them (inside an
``atomic()`` block) or flushes them immediately, keeping multi-step writes
atomic without a Unit of Work.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.entities.user import User
from domain.repositories.account_repository import AccountRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.email import Email
from infrastructure.django.apps.bank.models import (
    AccountModel,
    TransactionModel,
    UserModel,
)
from infrastructure.django.persistence.mappers import (
    account_to_domain,
    account_to_model,
    transaction_to_domain,
    transaction_to_model,
    user_to_domain,
    user_to_model,
)
from infrastructure.django.persistence.transaction import DjangoTransactionManager


class DjangoUserRepository(UserRepository):
    def __init__(self, transaction_manager: DjangoTransactionManager) -> None:
        self._tx = transaction_manager

    async def add(self, user: User) -> None:
        await self._tx.persist(user_to_model(user), is_new=True)

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await UserModel.objects.filter(id=user_id).afirst()
        return user_to_domain(model) if model else None

    async def get_by_email(self, email: Email) -> User | None:
        model = await UserModel.objects.filter(email=str(email)).afirst()
        return user_to_domain(model) if model else None

    async def exists_by_email(self, email: Email) -> bool:
        return await UserModel.objects.filter(email=str(email)).aexists()


class DjangoAccountRepository(AccountRepository):
    def __init__(self, transaction_manager: DjangoTransactionManager) -> None:
        self._tx = transaction_manager

    async def add(self, account: Account) -> None:
        await self._tx.persist(account_to_model(account), is_new=True)

    async def update(self, account: Account) -> None:
        await self._tx.persist(account_to_model(account), is_new=False)

    async def get_by_id(self, account_id: UUID) -> Account | None:
        model = await AccountModel.objects.filter(id=account_id).afirst()
        return account_to_domain(model) if model else None

    async def get_by_number(self, account_number: AccountNumber) -> Account | None:
        model = await AccountModel.objects.filter(
            account_number=str(account_number)
        ).afirst()
        return account_to_domain(model) if model else None

    async def list_by_owner(self, owner_id: UUID) -> Sequence[Account]:
        accounts: list[Account] = []
        async for model in (
            AccountModel.objects.filter(owner_id=owner_id).order_by("account_number")
        ):
            accounts.append(account_to_domain(model))
        return accounts


class DjangoTransactionRepository(TransactionRepository):
    def __init__(self, transaction_manager: DjangoTransactionManager) -> None:
        self._tx = transaction_manager

    async def add(self, transaction: Transaction) -> None:
        await self._tx.persist(transaction_to_model(transaction), is_new=True)

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        model = await TransactionModel.objects.filter(id=transaction_id).afirst()
        return transaction_to_domain(model) if model else None

    async def list_by_account(self, account_id: UUID) -> Sequence[Transaction]:
        transactions: list[Transaction] = []
        async for model in (
            TransactionModel.objects.filter(account_id=account_id).order_by(
                "created_at"
            )
        ):
            transactions.append(transaction_to_domain(model))
        return transactions
