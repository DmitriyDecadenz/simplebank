import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base domain event. Immutable fact that something happened."""

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID | None = None

    @property
    def event_type(self) -> str:
        return self.__class__.__name__

    def to_payload(self) -> dict[str, Any]:
        raise NotImplementedError