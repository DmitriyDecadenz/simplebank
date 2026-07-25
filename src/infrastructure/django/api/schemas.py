"""Ninja request/response schemas for the API layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class RegisterIn(Schema):
    email: str
    password: str


class LoginIn(Schema):
    email: str
    password: str


class AccountOut(Schema):
    id: UUID
    account_number: str
    balance: Decimal
    currency: str


class UserOut(Schema):
    id: UUID
    email: str
    account: AccountOut


class TokenOut(Schema):
    access_token: str
    token_type: str


class BalanceOut(Schema):
    account_number: str
    balance: Decimal
    currency: str


class TransferIn(Schema):
    to_account_number: str
    amount: Decimal
    currency: str = "EUR"


class TransferOut(Schema):
    from_account_number: str
    to_account_number: str
    amount: Decimal
    fee: Decimal
    total_debited: Decimal
    currency: str
    from_balance: Decimal
    to_balance: Decimal


class TransactionOut(Schema):
    amount: Decimal
    currency: str
    type: str
    created_at: datetime


class ErrorOut(Schema):
    detail: str
