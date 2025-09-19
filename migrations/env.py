import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

# Alembic Config object, provides access to values from alembic.ini
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def get_engine():
    """Return SQLAlchemy engine from Flask-Migrate/SQLAlchemy extension."""
    try:
        # Flask-SQLAlchemy < 3.0
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy >= 3.0
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """Get engine URL string for Alembic."""
    engine = get_engine()
    try:
        return engine.url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(engine.url).replace("%", "%%")


# Set Alembic sqlalchemy.url dynamically from Flask config
config.set_main_option("sqlalchemy.url", get_engine_url())

# Target metadata for 'autogenerate' support
target_db = current_app.extensions["migrate"].db


def get_metadata():
    """Return SQLAlchemy metadata for autogenerate support."""
    if hasattr(target_db, "metadatas"):  # Flask-SQLAlchemy >= 3
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode (no live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode (with live DB connection)."""

    def process_revision_directives(context, revision, directives):
        """Prevent empty auto-generated migrations."""
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    conf_args = current_app.extensions["migrate"].configure_args or {}
    conf_args.setdefault("process_revision_directives", process_revision_directives)

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()