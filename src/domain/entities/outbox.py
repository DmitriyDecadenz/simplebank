from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    id: UUID
    event_type: str
    aggregate_id: UUID
    payload: dict[str, object]
    correlation_id: UUID | None
    created_at: datetime
    published_at: datetime | None = None
    attempts: int = 0
    last_error: str | None = None
