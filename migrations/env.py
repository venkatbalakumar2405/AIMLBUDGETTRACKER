import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

# Alembic Config object (from alembic.ini)
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
    except (TypeError, AttributeError, KeyError):
        # Flask-SQLAlchemy >= 3.0
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """Get database URL for Alembic."""
    engine = get_engine()
    try:
        return engine.url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(engine.url).replace("%", "%%")


# ✅ Dynamically set sqlalchemy.url from Flask config
config.set_main_option("sqlalchemy.url", get_engine_url())

# Target metadata for autogenerate support
db = current_app.extensions["migrate"].db


def get_metadata():
    """Return SQLAlchemy metadata for migrations."""
    if hasattr(db, "metadatas"):  # Flask-SQLAlchemy >= 3.0
        return db.metadatas.get(None)
    return db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        compare_type=True,  # ✅ detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""

    def process_revision_directives(context, revision, directives):
        """Skip empty autogenerate migrations."""
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("✅ No schema changes detected.")

    conf_args = getattr(current_app.extensions["migrate"], "configure_args", {}) or {}
    conf_args.setdefault("process_revision_directives", process_revision_directives)

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            compare_type=True,  # ✅ detect column type changes
            **conf_args,
        )

        with context.begin_transaction():
            context.run_migrations()


# ✅ Choose run mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
