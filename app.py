from flask import Flask
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models so Flask-Migrate detects them
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import routes (blueprints)
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp


def create_app():
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Enable CORS for React frontend (localhost:5173)
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173"]}},
        supports_credentials=True
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Initialize background scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Example daily background job
    @scheduler.task("cron", id="daily_job", hour=0, minute=0)
    def daily_task():
        with app.app_context():
            print("✅ Daily scheduled task executed: checking expenses...")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)

    return app


if __name__ == "__main__":
    # Run app in development mode
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)