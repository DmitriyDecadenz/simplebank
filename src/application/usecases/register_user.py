"""RegisterUser use case.

Registers a new user and, in the same atomic transaction, opens an account for
them credited with a welcome bonus.
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
from application.transaction import TransactionManager
from domain.entities.account import Account
from domain.entities.user import User
from domain.ports.password_hasher import PasswordHasher
from domain.repositories.account_repository import AccountRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository
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
        self,
        users: UserRepository,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        password_hasher: PasswordHasher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._users = users
        self._accounts = accounts
        self._transactions = transactions
        self._hasher = password_hasher
        self._tx = transaction_manager

    async def execute(self, command: RegisterUserCommand) -> UserDTO:
        email = Email(command.email)

        # Uniqueness check.
        if await self._users.exists_by_email(email):
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
        async with self._tx.atomic():
            await self._users.add(user)
            await self._accounts.add(account)
            await self._transactions.add(transaction)

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
            if await self._accounts.get_by_number(candidate) is None:
                return candidate
        raise AccountNumberGenerationError(
            "Could not generate a unique account number; please retry"
        )
