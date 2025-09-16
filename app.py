import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models so SQLAlchemy is aware of them
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import blueprints
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp


def create_app():
    """Application factory for Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ================== LOGGING ==================
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ================== CORS CONFIG ==================
    _configure_cors(app)

    # ================== EXTENSIONS ==================
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    if app.debug:  # Auto-create tables in debug mode
        with app.app_context():
            db.create_all()
            app.logger.info("✅ Auto-created database tables in DEBUG mode")

    # ================== SCHEDULER ==================
    _configure_scheduler(app)

    # ================== BLUEPRINTS ==================
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)

    # ================== HEALTH CHECK ==================
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200

    # ================== ERROR HANDLING ==================
    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException

        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code

        app.logger.error("❌ Unhandled Exception", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app


def _configure_cors(app):
    """Configure CORS with dynamic frontend origin."""
    frontend_url = os.getenv("FRONTEND_URL", "*")

    CORS(
        app,
        resources={r"/*": {"origins": frontend_url}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    @app.after_request
    def apply_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed_origin = os.getenv("FRONTEND_URL", origin or "*")
        if origin and allowed_origin:
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "Access-Control-Request-Headers", "Content-Type, Authorization"
            )
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Vary"] = "Origin"
        return response


def _configure_scheduler(app):
    """Initialize and start the APScheduler with jobs."""
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task("cron", id="daily_job", hour=0, minute=0)
    def daily_task():
        with app.app_context():
            app.logger.info("✅ Daily task executed: checking expenses...")


if __name__ == "__main__":
    app = create_app()

    # Run server with env-configured host/port
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

    app.run(host=host, port=port, debug=debug)