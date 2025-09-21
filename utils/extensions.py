from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

# Core Flask extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


def init_extensions(app):
    """Initialize all Flask extensions with logging."""
    db.init_app(app)
    app.logger.info("✅ SQLAlchemy initialized")

    migrate.init_app(app, db)
    app.logger.info("✅ Flask-Migrate initialized")

    mail.init_app(app)
    app.logger.info("✅ Flask-Mail initialized")