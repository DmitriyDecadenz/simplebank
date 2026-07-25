"""NinjaAPI instance with routers and exception handlers.

Maps domain/application errors to HTTP responses so the layers below stay
framework-agnostic.
"""

from __future__ import annotations

from ninja import NinjaAPI

from application.exceptions import (
    AccountNotFoundError,
    ApplicationError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from domain.exceptions import DomainError
from infrastructure.django.api.routes import router

api = NinjaAPI(title="SimpleBank", version="1.0.0")
api.add_router("", router)


def _error(request, exc: Exception, status: int):
    return api.create_response(request, {"detail": str(exc)}, status=status)


@api.exception_handler(EmailAlreadyExistsError)
def _email_exists(request, exc):
    return _error(request, exc, 409)


@api.exception_handler(InvalidCredentialsError)
def _invalid_credentials(request, exc):
    return _error(request, exc, 401)


@api.exception_handler(AccountNotFoundError)
def _account_not_found(request, exc):
    return _error(request, exc, 404)


@api.exception_handler(ApplicationError)
def _application_error(request, exc):
    return _error(request, exc, 400)


@api.exception_handler(DomainError)
def _domain_error(request, exc):
    return _error(request, exc, 400)
