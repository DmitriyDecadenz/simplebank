"""Django ORM models for the bank domain.

These are pure persistence models; they carry no business logic. The domain
never references them, translation happens in the mappers module.
"""

from __future__ import annotations

from django.db import models

from domain.enums.transaction_type import TransactionType


class UserModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    email = models.CharField(max_length=320, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email


class AccountModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    owner = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="accounts",
        db_column="owner_id",
    )
    account_number = models.CharField(max_length=34, unique=True, db_index=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)

    class Meta:
        db_table = "accounts"

    def __str__(self) -> str:
        return self.account_number


class TransactionModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_column="account_id",
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)
    type = models.CharField(
        max_length=16,
        choices=[(t.value, t.value) for t in TransactionType],
    )
    created_at = models.DateTimeField()

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(
                fields=["account", "-created_at"],
                name="ix_tx_account_created",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.type} {self.amount} {self.currency}"
