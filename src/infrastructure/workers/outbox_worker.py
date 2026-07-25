from __future__ import annotations

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.persistence.repositories import SqlAlchemyOutboxRepository

from domain.ports.event_bus import EventPublisher

logger = structlog.get_logger(__name__)


class OutboxWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: EventPublisher,
        *,
        poll_interval: float = 1.0,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._publisher = publisher
        self._poll_interval = poll_interval
        self._batch_size = batch_size
        self._running = False

    async def run(self) -> None:
        self._running = True
        logger.info("outbox_worker_started")
        while self._running:
            try:
                processed = await self._process_batch()
                if processed == 0:
                    await asyncio.sleep(self._poll_interval)
            except Exception:
                logger.exception("outbox_worker_error")
                await asyncio.sleep(self._poll_interval)

    async def _process_batch(self) -> int:
        async with self._session_factory() as session:
            repo = SqlAlchemyOutboxRepository(session)
            messages = await repo.fetch_pending(self._batch_size)
            count = 0
            for msg in messages:
                try:
                    await self._publisher.publish(msg.event_type, msg.payload)
                    await repo.mark_published(msg.id)
                    count += 1
                except Exception as exc:
                    await repo.mark_failed(msg.id, str(exc))
                    logger.exception(
                        "outbox_publish_failed",
                        message_id=str(msg.id),
                        event_type=msg.event_type,
                    )
            await session.commit()
            if count:
                logger.info("outbox_batch_published", count=count)
            return count

    def stop(self) -> None:
        self._running = False

