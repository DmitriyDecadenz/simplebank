from typing import Protocol


class EventPublisher(Protocol):
    async def publish(self, event_type: str, payload: dict[str, object]) -> None: ...
