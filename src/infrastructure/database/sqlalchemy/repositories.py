"""SQLAlchemy implementations of the domain repository interfaces.

Every repository operates on an ``AsyncSession`` provided by the Unit of Work,
so all of their reads and writes participate in the same transaction. They
contain persistence logic only and delegate ORM<->domain translation to the
mappers module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.account import Account
from domain.entities.outbox import OutboxMessage
from domain.entities.transaction import Transaction
from domain.entities.user import User
from domain.event import DomainEvent
from domain.repositories.account_repository import AccountRepository
from domain.repositories.outbox_repository import OutboxRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.email import Email
from infrastructure.database.sqlalchemy.mappers import (
    account_to_domain,
    account_to_model,
    transaction_to_domain,
    transaction_to_model,
    user_to_domain,
    user_to_model,
)
from infrastructure.database.sqlalchemy.models import (
    AccountModel,
    OutboxModel,
    TransactionModel,
    UserModel,
)


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(user_to_model(user))

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return user_to_domain(model) if model else None

    async def get_by_email(self, email: Email) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == str(email))
        )
        model = result.scalar_one_or_none()
        return user_to_domain(model) if model else None

    async def exists_by_email(self, email: Email) -> bool:
        result = await self._session.execute(
            select(exists().where(UserModel.email == str(email)))
        )
        return bool(result.scalar())


class SqlAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: Account) -> None:
        self._session.add(account_to_model(account))

    async def update(self, account: Account) -> None:
        await self._session.merge(account_to_model(account))

    async def get_by_id(self, account_id: UUID) -> Account | None:
        model = await self._session.get(AccountModel, account_id)
        return account_to_domain(model) if model else None

    async def get_by_number(self, account_number: AccountNumber) -> Account | None:
        result = await self._session.execute(
            select(AccountModel).where(
                AccountModel.account_number == str(account_number)
            )
        )
        model = result.scalar_one_or_none()
        return account_to_domain(model) if model else None

    async def list_by_owner(self, owner_id: UUID) -> Sequence[Account]:
        result = await self._session.execute(
            select(AccountModel)
            .where(AccountModel.owner_id == owner_id)
            .order_by(AccountModel.account_number)
        )
        return [account_to_domain(model) for model in result.scalars().all()]


class SqlAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transaction: Transaction) -> None:
        self._session.add(transaction_to_model(transaction))

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        model = await self._session.get(TransactionModel, transaction_id)
        return transaction_to_domain(model) if model else None

    async def list_by_account(self, account_id: UUID) -> Sequence[Transaction]:
        result = await self._session.execute(
            select(TransactionModel)
            .where(TransactionModel.account_id == account_id)
            .order_by(TransactionModel.created_at)
        )
        return [transaction_to_domain(model) for model in result.scalars().all()]


class SqlAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: DomainEvent) -> None:
        self._session.add(
            OutboxModel(
                id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                payload=event.to_payload(),
                correlation_id=event.correlation_id,
                created_at=event.occurred_at,
            )
        )

    async def add_many(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            await self.add(event)

    async def fetch_pending(self, limit: int = 100) -> Sequence[OutboxMessage]:
        result = await self._session.execute(
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        messages = []
        for model in result.scalars().all():
            messages.append(
                OutboxMessage(
                    id=model.id,
                    event_type=model.event_type,
                    aggregate_id=model.aggregate_id,
                    payload=dict(model.payload),
                    correlation_id=model.correlation_id,
                    created_at=model.created_at,
                    published_at=model.published_at,
                    attempts=model.attempts,
                    last_error=model.last_error,
                )
            )
        return messages

    async def mark_published(self, message_id: UUID) -> None:
        await self._session.execute(
            update(OutboxModel)
            .where(OutboxModel.id == message_id)
            .values(published_at=datetime.now(UTC))
        )

    async def mark_failed(self, message_id: UUID, error: str) -> None:
        await self._session.execute(
            update(OutboxModel)
            .where(OutboxModel.id == message_id)
            .values(
                attempts=OutboxModel.attempts + 1,
                last_error=error[:2000],
            )
        )
