from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID as UUIDType

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UUID,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.enums.transaction_type import TransactionType

# Monetary precision: up to 18 integer digits + 2 fractional (matches Money).
_MONEY_NUMERIC = Numeric(precision=20, scale=2)
_CURRENCY_LENGTH = 3


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


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    accounts: Mapped[list["AccountModel"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_number: Mapped[str] = mapped_column(
        String(34), unique=True, nullable=False, index=True
    )
    balance: Mapped[Decimal] = mapped_column(_MONEY_NUMERIC, nullable=False)
    currency: Mapped[str] = mapped_column(String(_CURRENCY_LENGTH), nullable=False)

    owner: Mapped["UserModel"] = relationship(back_populates="accounts")
    transactions: Mapped[list["TransactionModel"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_account_created", "account_id", "created_at"),
    )

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(_MONEY_NUMERIC, nullable=False)
    currency: Mapped[str] = mapped_column(String(_CURRENCY_LENGTH), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account: Mapped["AccountModel"] = relationship(back_populates="transactions")
