from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models
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

    # ✅ Enable CORS for both 5173 & 5174 (React dev servers)
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5174"]}},
        supports_credentials=True
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Initialize and start scheduler
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task("cron", id="daily_job", hour=0, minute=0)
    def daily_task():
        with app.app_context():
            print("✅ Daily task executed: checking expenses...")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)

    # ✅ Global error handler (so frontend sees real errors)
    @app.errorhandler(Exception)
    def handle_exception(e):
        return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)