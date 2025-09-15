from flask import Flask
from config import Config
from utils.extensions import db, mail, scheduler  # noqa: F401
from flask_migrate import Migrate

# ✅ Import models so Flask-Migrate detects them
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # Register routes
    from routes.auth_routes import auth_bp
    from routes.budget_routes import budget_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")

    return app
