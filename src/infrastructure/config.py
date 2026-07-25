"""Application configuration via pydantic-settings.

Settings are composed from nested models, each loaded from environment variables
with a ``SECTION__KEY`` convention (e.g. ``POSTGRES__HOST``). The ``Settings``
object is constructed explicitly and passed through dependency injection; it is
never used as a global singleton.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = ".env"





class AppSettings(BaseSettings):
    """General application settings."""

    model_config = SettingsConfigDict(env_prefix="APP__", extra="ignore")

    log_level: str = Field(default="INFO", description="Root log level.")
    environment: str = Field(
        default="local", description="Deployment environment name."
    )
    json_logs: bool = Field(default=True, description="Emit JSON logs when true.")

    excluded_endpoints: list[str] = Field(
        default=[], description="Endpoints to exclude."
    )
    root_path: str = Field(default="/", description="Root path.")


class PostgresSettings(BaseSettings):
    """PostgreSQL connection settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES__", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="smr_express_validator")
    password: str = Field(default="smr_express_validator")
    db: str = Field(default="smr_express_validator")
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    echo: bool = Field(default=False)
    schemas: str = Field(default="smr_express_validator")

    @property
    def dsn(self) -> str:
        """Return the async SQLAlchemy DSN (asyncpg driver).

        Used both by the runtime engine and by Alembic, which runs migrations
        through an async engine to avoid a second (sync) driver dependency.
        """
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def sync_dsn(self) -> str:
        """Return the sync SQLAlchemy DSN (asyncpg driver).

        Used both by the runtime engine and by Alembic, which runs migrations
        through an async engine to avoid a second (sync) driver dependency.
        """
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RabbitMqSettings(BaseSettings):
    """Message broker (RabbitMQ) settings."""

    model_config = SettingsConfigDict(env_prefix="RABBITMQ__", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=5672)
    user: str = Field(default="smr_express_validator")
    password: str = Field(default="smr_express_validator")
    consumer_exchange: str = Field(default="smr_express_validator")
    consumer_queue: str = Field(default="validations.queue")
    enable_ssl: bool = Field(default=False, description="Enable SSL.")
    prefetch_count: int = Field(default=10, ge=1)

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class CorsSettings(BaseSettings):
    """CORS settings."""

    model_config = SettingsConfigDict(env_prefix="CORS__", extra="ignore")
    allow_origins: list = Field(default=["*"])
    allow_methods: list = Field(default=["*"])
    allow_headers: list = Field(default=["*"])
    allow_credentials: bool = Field(default=True)
    expose_headers: list = Field(default=["*"])
    max_age: int = Field(default=3600)


class Settings(BaseSettings):
    """Root settings aggregating every configuration section."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    app: AppSettings = Field(default_factory=AppSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    rabbit: RabbitMqSettings = Field(default_factory=RabbitMqSettings)


def load_settings() -> Settings:
    """Build a fresh :class:`Settings` instance from the environment.

    Returns:
        A fully populated settings object. Call this once at composition time
        and inject the result; do not turn it into a module-level global.
    """
    return Settings()
