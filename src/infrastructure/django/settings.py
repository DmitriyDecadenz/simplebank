"""Django settings, sourced from the pydantic ``Settings`` (single source of truth).

Besides our ``bank`` app (which exposes the ORM models), the standard Django
admin is enabled for internal inspection, so the contrib apps it needs (auth,
sessions, messages, contenttypes, staticfiles) are installed. The JSON API stays
JWT-based and CSRF-exempt (Django Ninja marks its views accordingly).

Values (DB, secret key) come from :func:`infrastructure.config.load_settings` so
there is one configuration origin.

Set the ``SIMPLEBANK_SQLITE`` env var to run against a local SQLite database
(used for tests and quick local runs); otherwise PostgreSQL from config is used.
"""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.config import load_settings

_settings = load_settings()

_BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = _settings.auth.secret_key
DEBUG = _settings.app.environment.lower() in {"local", "dev", "development"}
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "infrastructure.django.apps.bank.apps.BankConfig",
]

MIDDLEWARE = [
    # WhiteNoise serves the admin's static files under ASGI (no runserver).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "infrastructure.django.urls"

# Server-rendered pages (thin HTML UI) live in DIRS; APP_DIRS lets the admin
# load its own templates. Context processors are required by the admin.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [_BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

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

# Static files (served by WhiteNoise after `collectstatic`). _BASE_DIR is
# src/infrastructure/django; parents[2] is the project root (where manage.py is).
STATIC_URL = "static/"
STATIC_ROOT = _BASE_DIR.parents[2] / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

USE_TZ = True
TIME_ZONE = "UTC"
USE_I18N = False
