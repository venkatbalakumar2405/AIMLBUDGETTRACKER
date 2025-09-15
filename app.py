from flask import Flask
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models so Flask-Migrate can detect them
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import routes
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp


def create_app():
    """Application factory pattern for Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend-backend communication
    CORS(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Initialize and start scheduler
    scheduler.init_app(app)
    scheduler.start()

    # ✅ Example job: runs every day at midnight
    @scheduler.task("cron", id="daily_job", hour=0, minute=0)
    def daily_task():
        with app.app_context():
            print("✅ Daily task executed: checking expenses...")
            # Example: later, you can query DB or send reminder email
            # users = User.query.all()
            # for user in users:
            #     send_reminder(user.email)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)