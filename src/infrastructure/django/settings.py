"""Django settings, sourced from the pydantic ``Settings`` (single source of truth).

Django is used purely as infrastructure here: no admin, sessions or contrib.auth,
just our ``bank`` app exposing the ORM models. Values (DB, secret key) come from
:func:`infrastructure.config.load_settings` so there is one configuration origin.

Set the ``SIMPLEBANK_SQLITE`` env var to run against a local SQLite database
(used for tests and quick local runs); otherwise PostgreSQL from config is used.
"""

from __future__ import annotations

import os

from infrastructure.config import load_settings

_settings = load_settings()

SECRET_KEY = _settings.auth.secret_key
DEBUG = _settings.app.environment.lower() in {"local", "dev", "development"}
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "infrastructure.django.apps.bank.apps.BankConfig",
]

# Ninja serves everything; no session/auth/CSRF middleware needed for a token API.
MIDDLEWARE: list[str] = []

ROOT_URLCONF = "infrastructure.django.urls"

if os.environ.get("SIMPLEBANK_SQLITE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SIMPLEBANK_SQLITE_PATH", ":memory:"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _settings.postgres.db,
            "USER": _settings.postgres.user,
            "PASSWORD": _settings.postgres.password,
            "HOST": _settings.postgres.host,
            "PORT": str(_settings.postgres.port),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
TIME_ZONE = "UTC"
USE_I18N = False
