"""Translation between SQLAlchemy models and domain objects.

The domain layer is intentionally ignorant of the ORM, so these functions are
the single place where the two representations meet. They contain no business
logic: they only move data across the boundary and rebuild value objects.
"""

from __future__ import annotations

from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.entities.user import User
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.email import Email
from domain.value_objects.money import Money
from domain.value_objects.password_hash import PasswordHash
from infrastructure.database.sqlalchemy.models import (
    AccountModel,
    TransactionModel,
    UserModel,
)


def user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
    )


def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=str(user.email),
        password_hash=str(user.password_hash),
    )


def account_to_domain(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        owner_id=model.owner_id,
        account_number=AccountNumber(model.account_number),
        balance=Money(model.balance, model.currency),
    )


def account_to_model(account: Account) -> AccountModel:
    return AccountModel(
        id=account.id,
        owner_id=account.owner_id,
        account_number=str(account.account_number),
        balance=account.balance.amount,
        currency=account.balance.currency,
    )


def transaction_to_domain(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        account_id=model.account_id,
        amount=Money(model.amount, model.currency),
        type=model.type,
        created_at=model.created_at,
    )


def transaction_to_model(transaction: Transaction) -> TransactionModel:
    return TransactionModel(
        id=transaction.id,
        account_id=transaction.account_id,
        amount=transaction.amount.amount,
        currency=transaction.amount.currency,
        type=transaction.type,
        created_at=transaction.created_at,
    )
