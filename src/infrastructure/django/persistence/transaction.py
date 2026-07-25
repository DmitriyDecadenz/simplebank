"""Django implementation of the :class:`TransactionManager` port.

Django does not support keeping a transaction open across ``await`` points:
``transaction.atomic()`` must run synchronously. To offer an async atomic
boundary, this manager buffers every write performed inside ``atomic()`` and
flushes the whole batch in a single synchronous ``transaction.atomic()`` block
executed via ``sync_to_async(thread_sensitive=True)``.

The pending buffer is stored in a :class:`~contextvars.ContextVar`, so it is
isolated per async task and safe under concurrent requests, even though a single
manager instance is shared across the application.

Repositories call :meth:`persist` to schedule a write:
* inside an ``atomic()`` block the write is buffered and committed on exit;
* outside any block it is flushed immediately in its own atomic transaction.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import AsyncIterator, Callable, TypeVar
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import models, transaction

from application.transaction import AtomicContext, TransactionManager
from domain.entities.account import Account
from domain.entities.transaction import Transaction
from domain.value_objects.account_number import AccountNumber
from infrastructure.django.apps.bank.models import AccountModel, TransactionModel
from infrastructure.django.persistence.mappers import (
    account_to_domain,
    account_to_model,
    transaction_to_model,
)

_Pending = list[tuple[models.Model, bool]]
T = TypeVar("T")


class DjangoAtomicContext(AtomicContext):
    """Locking, synchronous repository operations for use inside ``run``.

    Must only be used while a database transaction is open; account reads issue
    ``SELECT ... FOR UPDATE`` and hold the lock until commit.
    """

    def find_account_id_by_number(self, account_number: AccountNumber) -> UUID | None:
        return (
            AccountModel.objects.filter(account_number=str(account_number))
            .values_list("id", flat=True)
            .first()
        )

    def get_account_for_update(self, account_id: UUID) -> Account | None:
        try:
            model = AccountModel.objects.select_for_update().get(id=account_id)
        except AccountModel.DoesNotExist:
            return None
        return account_to_domain(model)

    def save_account(self, account: Account) -> None:
        account_to_model(account).save(force_update=True)

    def add_transaction(self, transaction_entity: Transaction) -> None:
        transaction_to_model(transaction_entity).save(force_insert=True)


class DjangoTransactionManager(TransactionManager):
    def __init__(self) -> None:
        self._pending: ContextVar[_Pending | None] = ContextVar(
            "django_tx_pending", default=None
        )

    @asynccontextmanager
    async def atomic(self) -> AsyncIterator[None]:
        pending: _Pending = []
        token = self._pending.set(pending)
        try:
            yield
        except BaseException:
            # Nothing is written until we flush, so failing simply discards the
            # buffered writes.
            raise
        else:
            if pending:
                await self._flush(pending)
        finally:
            self._pending.reset(token)

    async def run(self, work: Callable[[AtomicContext], T]) -> T:
        return await self._run(work)

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def _run(work: Callable[[AtomicContext], T]) -> T:
        # A real, synchronous transaction: locks taken via select_for_update in
        # DjangoAtomicContext are held until this block commits.
        with transaction.atomic():
            return work(DjangoAtomicContext())

    async def persist(self, instance: models.Model, *, is_new: bool) -> None:
        """Schedule a model instance to be saved.

        Buffered when called inside :meth:`atomic`, otherwise written at once.
        """
        pending = self._pending.get()
        if pending is None:
            await self._flush([(instance, is_new)])
        else:
            pending.append((instance, is_new))

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def _flush(pending: _Pending) -> None:
        with transaction.atomic():
            for instance, is_new in pending:
                instance.save(force_insert=is_new, force_update=not is_new)
