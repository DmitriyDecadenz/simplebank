"""Dependency injection container (dishka) for the Django stack.

Wires the framework-agnostic application layer to the Django infrastructure:
repositories, the transaction manager, CQRS readers, password hasher, token
service and the use cases/queries. Repositories are injected into use cases
directly; atomicity is provided by the transaction manager.
"""

from __future__ import annotations

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide

from application.queries.get_balance import AccountBalanceReader, GetBalance
from application.queries.list_accounts import AccountsReader, ListAccounts
from application.queries.list_transactions import (
    ListTransactions,
    TransactionHistoryReader,
)
from application.transaction import TransactionManager
from application.usecases.login import Login
from application.usecases.register_user import RegisterUser
from application.usecases.transfer_money import TransferMoney
from domain.ports.password_hasher import PasswordHasher
from domain.ports.token_service import TokenService
from domain.repositories.account_repository import AccountRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.repositories.user_repository import UserRepository
from infrastructure.config import Settings, load_settings
from infrastructure.django.persistence.read_models import (
    DjangoAccountBalanceReader,
    DjangoAccountsReader,
    DjangoTransactionHistoryReader,
)
from infrastructure.django.persistence.repositories import (
    DjangoAccountRepository,
    DjangoTransactionRepository,
    DjangoUserRepository,
)
from infrastructure.django.persistence.transaction import DjangoTransactionManager
from infrastructure.jwt import JwtTokenService
from infrastructure.security import Pbkdf2PasswordHasher


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return load_settings()

    @provide(scope=Scope.APP)
    def password_hasher(self) -> PasswordHasher:
        return Pbkdf2PasswordHasher()

    @provide(scope=Scope.APP)
    def token_service(self, settings: Settings) -> TokenService:
        return JwtTokenService(
            secret_key=settings.auth.secret_key,
            algorithm=settings.auth.algorithm,
            access_token_expire_minutes=settings.auth.access_token_expire_minutes,
        )

    @provide(scope=Scope.APP)
    def accounts_reader(self) -> AccountsReader:
        return DjangoAccountsReader()

    @provide(scope=Scope.APP)
    def account_balance_reader(self) -> AccountBalanceReader:
        return DjangoAccountBalanceReader()

    @provide(scope=Scope.APP)
    def transaction_history_reader(self) -> TransactionHistoryReader:
        return DjangoTransactionHistoryReader()

    @provide(scope=Scope.APP)
    def transaction_manager(self) -> TransactionManager:
        return DjangoTransactionManager()

    @provide(scope=Scope.APP)
    def user_repository(
        self, transaction_manager: TransactionManager
    ) -> UserRepository:
        return DjangoUserRepository(transaction_manager)

    @provide(scope=Scope.APP)
    def account_repository(
        self, transaction_manager: TransactionManager
    ) -> AccountRepository:
        return DjangoAccountRepository(transaction_manager)

    @provide(scope=Scope.APP)
    def transaction_repository(
        self, transaction_manager: TransactionManager
    ) -> TransactionRepository:
        return DjangoTransactionRepository(transaction_manager)

    @provide(scope=Scope.REQUEST)
    def register_user(
        self,
        users: UserRepository,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        password_hasher: PasswordHasher,
        transaction_manager: TransactionManager,
    ) -> RegisterUser:
        return RegisterUser(
            users, accounts, transactions, password_hasher, transaction_manager
        )

    @provide(scope=Scope.REQUEST)
    def login(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> Login:
        return Login(users, password_hasher, token_service)

    @provide(scope=Scope.REQUEST)
    def transfer_money(
        self,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        transaction_manager: TransactionManager,
    ) -> TransferMoney:
        return TransferMoney(accounts, transactions, transaction_manager)

    @provide(scope=Scope.REQUEST)
    def list_accounts(self, reader: AccountsReader) -> ListAccounts:
        return ListAccounts(reader)

    @provide(scope=Scope.REQUEST)
    def get_balance(self, reader: AccountBalanceReader) -> GetBalance:
        return GetBalance(reader)

    @provide(scope=Scope.REQUEST)
    def list_transactions(
        self, reader: TransactionHistoryReader
    ) -> ListTransactions:
        return ListTransactions(reader)


container: AsyncContainer = make_async_container(AppProvider())
