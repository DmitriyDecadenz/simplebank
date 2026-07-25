"""Login use case.

Authenticates a user by email/password and issues a JWT access token.
"""

from __future__ import annotations

from application.dto import LoginCommand, TokenDTO
from application.exceptions import InvalidCredentialsError
from application.unit_of_work import AbstractUnitOfWork
from domain.ports.password_hasher import PasswordHasher
from domain.ports.token_service import TokenService
from domain.value_objects.email import Email


class Login:
    """Verify credentials and return a signed access token."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._hasher = password_hasher
        self._tokens = token_service

    async def execute(self, command: LoginCommand) -> TokenDTO:
        email = Email(command.email)

        # 1. Find the user.
        async with self._uow:
            user = await self._uow.users.get_by_email(email)

        # 2. Verify the password. Use the same error for "no user" and "wrong
        #    password" to avoid leaking which emails are registered.
        if user is None or not self._hasher.verify(
            command.password, str(user.password_hash)
        ):
            raise InvalidCredentialsError("Invalid email or password")

        # 3. Generate the access token.
        access_token = self._tokens.create_access_token(
            subject=str(user.id), claims={"email": str(user.email)}
        )
        return TokenDTO(access_token=access_token)
