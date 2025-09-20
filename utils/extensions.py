from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask import Flask

# ================== Flask Extensions ==================
# These are initialized without an app context
# They will be bound later in app.py using init_app()

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
mail: Mail = Mail()
scheduler: APScheduler = APScheduler()


def init_extensions(app: Flask) -> None:
    """
    Initialize all Flask extensions with the given app.
    Call this inside create_app(app) or after app = Flask(__name__).

    Example:
        from utils.extensions import init_extensions
        app = Flask(__name__)
        init_extensions(app)
    """
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    scheduler.init_app(app)