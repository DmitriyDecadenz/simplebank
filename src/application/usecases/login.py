"""Login use case.

Authenticates a user by email/password and issues a JWT access token.
"""

from __future__ import annotations

from application.dto import LoginCommand, TokenDTO
from application.exceptions import InvalidCredentialsError
from domain.ports.password_hasher import PasswordHasher
from domain.ports.token_service import TokenService
from domain.repositories.user_repository import UserRepository
from domain.value_objects.email import Email


class Login:
    """Verify credentials and return a signed access token."""

    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._users = users
        self._hasher = password_hasher
        self._tokens = token_service

    async def execute(self, command: LoginCommand) -> TokenDTO:
        email = Email(command.email)

        # Find the user (read-only, no transaction needed).
        user = await self._users.get_by_email(email)

        # Verify the password. Same error for "no user" and "wrong password".
        if user is None or not self._hasher.verify(
            command.password, str(user.password_hash)
        ):
            raise InvalidCredentialsError("Invalid email or password")

        # Generate the access token.
        access_token = self._tokens.create_access_token(
            subject=str(user.id), claims={"email": str(user.email)}
        )
        return TokenDTO(access_token=access_token)
