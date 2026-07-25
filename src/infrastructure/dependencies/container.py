import ssl
from pathlib import Path
from typing import AsyncIterable

from dishka import Provider, Scope, provide, AsyncContainer, make_async_container
from faststream.rabbit import RabbitBroker
from faststream.security import BaseSecurity
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from src.application.unit_of_work import AbstractUnitOfWork
from src.application.use_cases.validate_event_use_case import ValidateEventUseCase
from src.application.use_cases.validate_pre_calculation_use_case import (
    ValidatePreCalculationUseCase,
)
from src.application.use_cases.validate_pre_creation_use_case import (
    ValidatePreCreationUseCase,
)
from src.domain.ports import (
    TerritoryGateway,
    ContractsGateway,
)
from src.domain.services.validation_engine import ValidationEngine
from src.domain.validation_rules.registry import ValidationRulesRegistry
from src.infrastructure.config import Settings, load_settings
from src.infrastructure.db.sqlalchemy.config import create_engine
from src.infrastructure.db.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.gateways import (
    HttpTerritoryGateway,
    HttpContractsGateway,
)


class BrokerProvider(Provider):

    @provide(scope=Scope.APP)
    async def settings(self) -> Settings:
        return load_settings()

    @provide(scope=Scope.APP)
    async def broker(self, settings: Settings) -> RabbitBroker:
        ssl_stx = ssl.create_default_context()
        security = BaseSecurity(ssl_context=ssl_stx)
        if settings.rabbit.enable_ssl:
            broker = RabbitBroker(settings.rabbit.url, security=security)
        else:
            broker = RabbitBroker(settings.rabbit.url)
        return broker


class AppProvider(Provider):

    @provide(scope=Scope.APP)
    async def settings(self) -> Settings:
        return load_settings()

    @provide(scope=Scope.APP)
    async def broker(self, settings: Settings) -> RabbitBroker:
        ssl_stx = ssl.create_default_context()
        security = BaseSecurity(ssl_context=ssl_stx)
        if settings.RABBITMQ_ENABLE_SSL:
            broker = RabbitBroker(settings.broker.url, security=security)
        else:
            broker = RabbitBroker(settings.broker.url)
        return broker

    @provide(scope=Scope.APP)
    def engine(
        self,
        settings: Settings,
    ) -> AsyncEngine:
        return create_engine(settings)

    @provide(scope=Scope.APP)
    def session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )

    @provide(scope=Scope.APP)
    async def http_client(self) -> AsyncIterable[AsyncClient]:
        project_root = Path(__file__).resolve().parents[3]
        cert_path = project_root / "sogaz-bundle-ca.crt"

        async with AsyncClient(timeout=30.0, verify=str(cert_path)) as client:
            yield client

    @provide(scope=Scope.REQUEST)
    def unit_of_work(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AbstractUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    ####
    # provide gateways, repos


container: AsyncContainer = make_async_container(
    AppProvider(),
    BrokerProvider(),
)
