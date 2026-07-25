import ssl

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker
from faststream.security import BaseSecurity
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from application.queries.get_balance import AccountBalanceReader, GetBalance
from application.unit_of_work import AbstractUnitOfWork
from application.usecases.login import Login
from application.usecases.register_user import RegisterUser
from domain.ports.password_hasher import PasswordHasher
from domain.ports.token_service import TokenService
from infrastructure.config import Settings, load_settings
from infrastructure.database.sqlalchemy.config import (
    create_engine,
    create_session_factory,
)
from infrastructure.database.sqlalchemy.read_models import (
    SqlAlchemyAccountBalanceReader,
)
from infrastructure.database.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.jwt import JwtTokenService
from infrastructure.security import Pbkdf2PasswordHasher


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def settings(self) -> Settings:
        return load_settings()

    @provide(scope=Scope.APP)
    def engine(self, settings: Settings) -> AsyncEngine:
        return create_engine(settings)

    @provide(scope=Scope.APP)
    def session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

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
    def account_balance_reader(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AccountBalanceReader:
        # CQRS read side: independent of the write-side Unit of Work.
        return SqlAlchemyAccountBalanceReader(session_factory)

    @provide(scope=Scope.REQUEST)
    def unit_of_work(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AbstractUnitOfWork:
        # Repositories are exposed exclusively through the Unit of Work, so no
        # repository is registered on its own: consumers receive the UoW and use
        # `uow.users`, `uow.accounts`, `uow.transactions` within one transaction.
        return SqlAlchemyUnitOfWork(session_factory)

    @provide(scope=Scope.REQUEST)
    def register_user(
        self, uow: AbstractUnitOfWork, password_hasher: PasswordHasher
    ) -> RegisterUser:
        return RegisterUser(uow, password_hasher)

    @provide(scope=Scope.REQUEST)
    def login(
        self,
        uow: AbstractUnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> Login:
        return Login(uow, password_hasher, token_service)

    @provide(scope=Scope.REQUEST)
    def get_balance(self, reader: AccountBalanceReader) -> GetBalance:
        return GetBalance(reader)


container: AsyncContainer = make_async_container(AppProvider())
