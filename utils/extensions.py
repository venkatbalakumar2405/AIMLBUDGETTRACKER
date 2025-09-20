from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

# Core extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
scheduler = BackgroundScheduler()

def init_extensions(app):
    """Initialize Flask extensions with the app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    scheduler.start()