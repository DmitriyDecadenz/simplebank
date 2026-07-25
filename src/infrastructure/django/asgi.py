"""ASGI entrypoint for the async Django + Ninja application."""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infrastructure.django.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
