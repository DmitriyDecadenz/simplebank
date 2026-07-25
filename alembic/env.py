from logging.config import fileConfig
import sys
from pathlib import Path

from src.infrastructure.config import load_settings

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from src.infrastructure.database.sqlalchemy.models import Base
from src.infrastructure.database.sqlalchemy.models import OutboxModel

settings = load_settings()

config = context.config
config.set_main_option("sqlalchemy.url", settings.postgres.sync_dsn)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="your_schema_db", #todo поменять на свою схему
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS your_schema_db")) #todo поменять на свою схему
        connection.execute(text("SET search_path TO your_schema_db, public")) #todo поменять на свою схему
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema="your_schema_db", #todo поменять на свою схему
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
