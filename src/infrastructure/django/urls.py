"""Root URL configuration: mounts the Ninja API at the site root."""

from __future__ import annotations

from django.urls import path

from infrastructure.django.api import api

urlpatterns = [
    path("", api.urls),
]
