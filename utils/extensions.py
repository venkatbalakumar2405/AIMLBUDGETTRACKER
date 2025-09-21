from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

# ---------------- CORE FLASK EXTENSIONS ---------------- #
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
mail: Mail = Mail()


def init_extensions(app: Flask) -> None:
    """
    Initialize all Flask extensions safely with logging.
    This prevents double-initialization issues and ensures
    each extension is bound to the given app context.
    """
    try:
        if not hasattr(app, "extensions") or "sqlalchemy" not in app.extensions:
            db.init_app(app)
            app.logger.info("✅ SQLAlchemy initialized")
        else:
            app.logger.debug("ℹ️ SQLAlchemy already initialized")

        if not hasattr(app, "extensions") or "migrate" not in app.extensions:
            migrate.init_app(app, db)
            app.logger.info("✅ Flask-Migrate initialized")
        else:
            app.logger.debug("ℹ️ Flask-Migrate already initialized")

        if not hasattr(app, "extensions") or "mail" not in app.extensions:
            mail.init_app(app)
            app.logger.info("✅ Flask-Mail initialized")
        else:
            app.logger.debug("ℹ️ Flask-Mail already initialized")

    except Exception as e:
        app.logger.exception("❌ Failed to initialize extensions: %s", e)
        raise
