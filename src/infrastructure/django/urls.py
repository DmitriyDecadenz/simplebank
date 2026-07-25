"""Root URL configuration.

Serves the thin HTML UI (login/register/dashboard) and mounts the Ninja API at
the site root. Page routes are declared before the API so their fixed paths take
precedence.
"""

from __future__ import annotations

from django.urls import path
from django.views.generic import TemplateView

from infrastructure.django.api import api

urlpatterns = [
    path("", TemplateView.as_view(template_name="login.html"), name="login-page"),
    path(
        "register",
        TemplateView.as_view(template_name="register.html"),
        name="register-page",
    ),
    path(
        "dashboard",
        TemplateView.as_view(template_name="dashboard.html"),
        name="dashboard-page",
    ),
    path("", api.urls),
]
