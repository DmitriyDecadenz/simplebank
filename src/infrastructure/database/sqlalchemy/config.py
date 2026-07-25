"""Async SQLAlchemy engine and session factory wiring."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config import load_settings, Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the async engine backed by asyncpg.

    Args:
        settings: PostgreSQL connection settings.

    Returns:
        A configured :class:`AsyncEngine`. The caller owns its lifecycle and is
        responsible for disposing it on shutdown.
    """
    settings = settings or load_settings()
    return create_async_engine(
        settings.postgres.dsn,
        echo=settings.postgres.echo,
        pool_size=settings.postgres.pool_size,
        max_overflow=settings.postgres.max_overflow,
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine.

    Args:
        engine: The async engine sessions will use.

    Returns:
        An ``async_sessionmaker`` producing ``AsyncSession`` instances with
        ``expire_on_commit`` disabled so committed objects remain usable.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
