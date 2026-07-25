from datetime import datetime

from sqlalchemy import Index, UUID, String, DateTime, func, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass

class OutboxModel(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index(
            "ix_outbox_pending",
            "published_at",
            postgresql_where="published_at IS NULL",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    correlation_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)