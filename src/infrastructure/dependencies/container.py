import ssl

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker
from faststream.security import BaseSecurity
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from application.unit_of_work import AbstractUnitOfWork
from application.usecases.register_user import RegisterUser
from domain.ports.password_hasher import PasswordHasher
from infrastructure.config import Settings, load_settings
from infrastructure.database.sqlalchemy.config import (
    create_engine,
    create_session_factory,
)
from infrastructure.database.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
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


container: AsyncContainer = make_async_container(AppProvider())
