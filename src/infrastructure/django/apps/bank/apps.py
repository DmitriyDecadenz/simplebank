from __future__ import annotations

from django.apps import AppConfig


class BankConfig(AppConfig):
    name = "infrastructure.django.apps.bank"
    label = "bank"
    default_auto_field = "django.db.models.BigAutoField"
