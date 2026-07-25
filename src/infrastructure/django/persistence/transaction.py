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
from typing import AsyncIterator

from asgiref.sync import sync_to_async
from django.db import models, transaction

from application.transaction import TransactionManager

_Pending = list[tuple[models.Model, bool]]


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
