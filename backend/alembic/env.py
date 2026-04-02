"""
Alembic environment configuration.

Uses synchronous SQLAlchemy connection to run migrations.
DATABASE_URL is loaded from application settings so the same .env
file controls both the application and migration tool.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Interpret the alembic.ini file for Python logging if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import application metadata ──────────────────────────────────────────────
# app.db.base imports every model so they are all reflected in Base.metadata
from app.db.base import Base  # noqa: E402
from app.core.config import settings  # noqa: E402

target_metadata = Base.metadata

# Override the sqlalchemy.url from settings so .env drives migrations
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Emits migration SQL to stdout without connecting to the database.
    Useful for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with a live DB connection.

    This is the normal operating mode when running ``alembic upgrade head``.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
