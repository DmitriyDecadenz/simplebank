"""Unit tests for the Login use case."""

from __future__ import annotations

import pytest

from application.dto import LoginCommand
from application.exceptions import InvalidCredentialsError
from application.usecases.login import Login
from conftest import make_user


@pytest.fixture
def use_case(users, password_hasher, token_service):
    return Login(users, password_hasher, token_service)


async def test_login_returns_token_for_valid_credentials(
    use_case, users, token_service
):
    user = make_user(email="alice@example.com", password="s3cret!!")
    users.preload(user)

    dto = await use_case.execute(
        LoginCommand(email="alice@example.com", password="s3cret!!")
    )

    assert dto.access_token == f"token-for-{user.id}"
    assert dto.token_type == "bearer"
    # Token was issued for that user, carrying the email claim.
    subject, claims = token_service.calls[0]
    assert subject == str(user.id)
    assert claims == {"email": "alice@example.com"}


async def test_login_rejects_wrong_password(use_case, users):
    users.preload(make_user(email="alice@example.com", password="correct"))

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginCommand(email="alice@example.com", password="wrong")
        )


async def test_login_rejects_unknown_email(use_case, token_service):
    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginCommand(email="ghost@example.com", password="whatever")
        )
    # No token minted for a failed login.
    assert token_service.calls == []
