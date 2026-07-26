"""Django admin registrations for the bank persistence models.

Edits here bypass domain rules (fees, balance invariants, hashing). The admin is
for inspection and support; day-to-day money movement must go through the API /
use cases. Ledger rows (transactions) are read-only.
"""

from __future__ import annotations

from django.contrib import admin

from infrastructure.django.apps.bank.models import (
    AccountModel,
    TransactionModel,
    UserModel,
)

admin.site.site_header = "SimpleBank Admin"
admin.site.site_title = "SimpleBank"
admin.site.index_title = "Bank data"


@admin.register(UserModel)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "id")
    search_fields = ("email", "id")
    ordering = ("email",)
    readonly_fields = ("id", "password_hash")


@admin.register(AccountModel)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "owner", "balance", "currency", "id")
    search_fields = ("account_number", "owner__email", "id")
    list_filter = ("currency",)
    autocomplete_fields = ("owner",)
    readonly_fields = ("id", "account_number")


@admin.register(TransactionModel)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "account", "type", "amount", "currency", "id")
    search_fields = ("id", "account__account_number")
    list_filter = ("type", "currency")
    date_hierarchy = "created_at"
    autocomplete_fields = ("account",)
    # Immutable ledger: view only.
    readonly_fields = ("id", "account", "amount", "currency", "type", "created_at")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
