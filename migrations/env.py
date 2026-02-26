from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import Flask app and db for metadata
from webapp.app import app, db
from webapp import models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except (KeyError, FileNotFoundError):
        # fileConfig may raise KeyError if the logging config is incomplete
        # (e.g. missing [formatters] section in certain environments).
        # Logging setup is non-critical so we skip it rather than block migrations.
        pass

# Set SQLAlchemy URL from Flask config or environment
db_url = os.environ.get("DATABASE_URL", app.config.get("SQLALCHEMY_DATABASE_URI"))
if not db_url:
    raise RuntimeError("DATABASE_URL must be set for migrations.")
config.set_main_option("sqlalchemy.url", db_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = db.metadata

# Use offline mode for autogenerate if database isn't available
is_autogenerate = sys.argv[0].endswith("alembic") and "--autogenerate" in sys.argv


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if is_autogenerate or context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
