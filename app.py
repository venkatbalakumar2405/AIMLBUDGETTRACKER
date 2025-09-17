import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models so SQLAlchemy is aware
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import blueprints
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp


def create_app():
    """Application factory for the Budget Tracker API."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ================== LOGGING ==================
    _configure_logging(app)

    # ================== EXTENSIONS ==================
    _initialize_extensions(app)

    # ================== CORS CONFIG ==================
    _configure_cors(app)

    # ================== BLUEPRINTS ==================
    _register_blueprints(app)

    # ================== HEALTH CHECK ==================
    _register_health_check(app)

    # ================== ERROR HANDLING ==================
    _register_error_handlers(app)

    # ================== SCHEDULER ==================
    _configure_scheduler(app)

    return app


# ---------------------- HELPERS ---------------------- #

def _configure_logging(app):
    """Configure logging format and level."""
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.info("✅ Logging configured")


def _initialize_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    if app.debug:
        with app.app_context():
            db.create_all()
            app.logger.info("✅ Auto-created database tables in DEBUG mode")


def _configure_cors(app):
    """Configure CORS with frontend URL from config."""
    frontend_url = app.config.get("FRONTEND_URL", "*")

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
        allowed_origin = frontend_url if frontend_url != "*" else origin or "*"
        if origin and allowed_origin:
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "Access-Control-Request-Headers", "Content-Type, Authorization"
            )
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Vary"] = "Origin"
        return response


def _register_blueprints(app):
    """Register application blueprints."""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)
    app.logger.info("✅ Blueprints registered")


def _register_health_check(app):
    """Register health check endpoint."""
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200


def _register_error_handlers(app):
    """Global error handler for HTTP and unexpected exceptions."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code

        app.logger.error("❌ Unhandled Exception", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def _configure_scheduler(app):
    """Initialize and configure APScheduler jobs."""
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task("cron", id="daily_job", hour=0, minute=0)
    def daily_task():
        with app.app_context():
            app.logger.info("✅ Daily task executed: checking expenses...")


# ---------------------- ENTRY POINT ---------------------- #

if __name__ == "__main__":
    app = create_app()

    app.run(
        host=app.config.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=app.config.get("FLASK_RUN_PORT", 5000),
        debug=app.config.get("FLASK_DEBUG", True),
    )