from datetime import datetime, UTC
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.outbox import OutboxMessage
from domain.event import DomainEvent
from infrastructure.database.sqlalchemy.models import OutboxModel


def _to_domain(model: ValidationRuleModel) -> ValidationRuleConfig:
    return ValidationRuleConfig(
        code=model.code,
        operation=ValidationOperation(model.operation),
        enabled=model.enabled,
        priority=model.priority,
        stop_on_fail=model.stop_on_fail,
        notification_type=model.notification_type,
        title=model.title,
        message=model.message,
        parameters={p.parameter_name: p.parameter_value for p in model.parameters},
    )


class SqlAlchemyExampleRepository(ValidationRuleRepository):
    """Deprecated EXAMPLE Реализация ValidationRuleRepository на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_operation(
        self, operation: ValidationOperation
    ) -> list[ValidationRuleConfig]:
        stmt = (
            select(ValidationRuleModel)
            .where(ValidationRuleModel.operation == operation.value)
            .options(selectinload(ValidationRuleModel.parameters))
            .order_by(ValidationRuleModel.priority)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars().all()]

    async def get_all(self) -> list[ValidationRuleConfig]:
        stmt = (
            select(ValidationRuleModel)
            .options(selectinload(ValidationRuleModel.parameters))
            .order_by(ValidationRuleModel.operation, ValidationRuleModel.priority)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars().all()]

    async def get_by_code(self, code: str) -> ValidationRuleConfig | None:
        stmt = (
            select(ValidationRuleModel)
            .where(ValidationRuleModel.code == code)
            .options(selectinload(ValidationRuleModel.parameters))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def update(self, config: ValidationRuleConfig) -> ValidationRuleConfig:
        stmt = (
            select(ValidationRuleModel)
            .where(ValidationRuleModel.code == config.code)
            .options(selectinload(ValidationRuleModel.parameters))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.enabled = config.enabled
        model.priority = config.priority
        model.stop_on_fail = config.stop_on_fail
        model.notification_type = config.notification_type
        model.title = config.title
        model.message = config.message
        model.parameters.clear()
        for name, value in config.parameters.items():
            model.parameters.append(
                ValidationRuleParameterModel(
                    id=uuid4(),
                    rule_code=config.code,
                    parameter_name=name,
                    parameter_value=value,
                )
            )
        await self._session.flush()
        return _to_domain(model)


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
