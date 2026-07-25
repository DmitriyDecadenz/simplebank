"""RegisterUser use case.

Registers a new user and, in the same transaction, opens an account for them
credited with a welcome bonus.
"""

from __future__ import annotations

import secrets
from decimal import Decimal
from uuid import uuid4

from application.dto import AccountDTO, RegisterUserCommand, UserDTO
from application.exceptions import (
    AccountNumberGenerationError,
    EmailAlreadyExistsError,
)
from application.unit_of_work import AbstractUnitOfWork
from domain.entities.account import Account
from domain.entities.user import User
from domain.ports.password_hasher import PasswordHasher
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.email import Email
from domain.value_objects.money import Money
from domain.value_objects.password_hash import PasswordHash

_ACCOUNT_NUMBER_DIGITS = 10
_ACCOUNT_NUMBER_MAX_ATTEMPTS = 10
_WELCOME_BONUS = Money(Decimal("10000"), "EUR")


class RegisterUser:
    """Create a user with an auto-opened, bonus-funded account."""

    def __init__(
        self, uow: AbstractUnitOfWork, password_hasher: PasswordHasher
    ) -> None:
        self._uow = uow
        self._hasher = password_hasher

    async def execute(self, command: RegisterUserCommand) -> UserDTO:
        email = Email(command.email)

        async with self._uow:
            # Uniqueness check.
            if await self._uow.users.exists_by_email(email):
                raise EmailAlreadyExistsError(f"Email already registered: {email}")

            # Hash the password and build the user.
            password_hash = PasswordHash(self._hasher.hash(command.password))
            user = User(id=uuid4(), email=email, password_hash=password_hash)

            # Generate a unique 10-digit account number and open the account.
            account_number = await self._generate_account_number()
            account = Account(
                id=uuid4(),
                owner_id=user.id,
                account_number=account_number,
                balance=Money.zero(_WELCOME_BONUS.currency),
            )

            # Credit the welcome bonus; the domain emits the CREDIT transaction.
            transaction = account.deposit(_WELCOME_BONUS)

            # Persist everything atomically.
            await self._uow.users.add(user)
            await self._uow.accounts.add(account)
            await self._uow.transactions.add(transaction)
            await self._uow.commit()

        return UserDTO(
            id=user.id,
            email=str(user.email),
            account=AccountDTO(
                id=account.id,
                account_number=str(account.account_number),
                balance=account.balance.amount,
                currency=account.balance.currency,
            ),
        )

    async def _generate_account_number(self) -> AccountNumber:
        """Generate a random 10-digit number not yet used by any account."""
        for _ in range(_ACCOUNT_NUMBER_MAX_ATTEMPTS):
            # First digit 1-9 to guarantee exactly 10 significant digits.
            digits = str(secrets.randbelow(9) + 1) + "".join(
                str(secrets.randbelow(10)) for _ in range(_ACCOUNT_NUMBER_DIGITS - 1)
            )
            candidate = AccountNumber(digits)
            if await self._uow.accounts.get_by_number(candidate) is None:
                return candidate
        raise AccountNumberGenerationError(
            "Could not generate a unique account number; please retry"
        )
