"""Django ORM read-side (CQRS query) implementations.

These bypass the domain aggregates and the Unit of Work, selecting only the
columns each query needs and returning projection DTOs directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from application.dto import AccountDTO, BalanceDTO, TransactionListItemDTO
from application.queries.get_balance import AccountBalanceReader
from application.queries.list_accounts import AccountsReader
from application.queries.list_transactions import TransactionHistoryReader
from infrastructure.django.apps.bank.models import AccountModel, TransactionModel


class DjangoAccountsReader(AccountsReader):
    async def list_by_owner(self, owner_id: UUID) -> Sequence[AccountDTO]:
        rows = (
            AccountModel.objects.filter(owner_id=owner_id)
            .order_by("account_number")
            .values("id", "account_number", "balance", "currency")
        )
        accounts: list[AccountDTO] = []
        async for row in rows:
            accounts.append(
                AccountDTO(
                    id=row["id"],
                    account_number=row["account_number"],
                    balance=row["balance"],
                    currency=row["currency"],
                )
            )
        return accounts


class DjangoAccountBalanceReader(AccountBalanceReader):
    async def get_balance(self, account_id: UUID) -> BalanceDTO | None:
        row = (
            await AccountModel.objects.filter(id=account_id)
            .values("account_number", "balance", "currency")
            .afirst()
        )
        if row is None:
            return None
        return BalanceDTO(
            account_number=row["account_number"],
            balance=row["balance"],
            currency=row["currency"],
        )


class DjangoTransactionHistoryReader(TransactionHistoryReader):
    async def list_transactions(
        self,
        account_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> Sequence[TransactionListItemDTO]:
        queryset = TransactionModel.objects.filter(account_id=account_id)
        if date_from is not None:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to is not None:
            queryset = queryset.filter(created_at__lte=date_to)
        queryset = queryset.order_by("-created_at").values(
            "amount", "currency", "type", "created_at"
        )

        items: list[TransactionListItemDTO] = []
        async for row in queryset:
            items.append(
                TransactionListItemDTO(
                    amount=row["amount"],
                    currency=row["currency"],
                    type=str(row["type"]),
                    created_at=row["created_at"],
                )
            )
        return items
