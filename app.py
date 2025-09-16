import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models (ensures they are registered with SQLAlchemy)
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import routes
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp


def create_app():
    """Application factory for Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Dynamic CORS setup
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},  # Allow all origins
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Optional: tighten security in production
    @app.after_request
    def apply_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed_origin = os.getenv("FRONTEND_URL", origin)  # ✅ Use env or fallback to request origin
        if origin and allowed_origin:
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Vary"] = "Origin"
        return response

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

    # ✅ Centralized error handling
    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()

    # ✅ Read host/port from environment with safe defaults
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

    app.run(host=host, port=port, debug=debug)