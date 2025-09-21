import os
import sys
import io
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

# ================== Project Imports ================== #
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from utils.extensions import db, init_extensions
from utils.scheduler_jobs import register_jobs

# Blueprints
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.expense_routes import expense_bp
from routes.salary_routes import salary_bp
from routes.trends_routes import trends_bp
from routes.home_routes import home_bp


# ✅ Ensure UTF-8 logs (Windows safe)
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# ---------------- APP FACTORY ---------------- #
def create_app(config_class: type[Config] = DevelopmentConfig) -> Flask:
    """Application factory for Budget Tracker API."""
    app = Flask(__name__)

    # Load config
    app.config.from_object(config_class)

    # Configure and initialize components
    _configure_logging(app)
    _normalize_and_log_db_uri(app)
    _initialize_extensions(app)
    _check_database_connection(app)
    _configure_cors(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_scheduler(app)

    return app


# ---------------- HELPERS ---------------- #
def _configure_logging(app: Flask) -> None:
    """Configure logging with rotation + console output."""
    log_level = logging.DEBUG if app.debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    if not app.logger.handlers:  # Prevent duplicate handlers
        logging.basicConfig(level=log_level, format=log_format)
        app.logger.setLevel(log_level)

        log_dir = app.config.get("LOG_DIR", os.getenv("LOG_DIR", "logs"))
        log_file = app.config.get("LOG_FILE", os.getenv("LOG_FILE", "budget_tracker.log"))
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, log_file),
            maxBytes=int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024)),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", 5)),
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

    app.logger.info("📝 Logging configured (level=%s)", logging.getLevelName(log_level))


def _normalize_and_log_db_uri(app: Flask) -> None:
    """Normalize DB URI (fix postgres://) and mask password in logs."""
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", ""))

    if not db_uri:
        app.logger.critical("❌ No SQLALCHEMY_DATABASE_URI configured. Exiting...")
        sys.exit(1)

    if db_uri.startswith("postgres://"):  # Fix deprecated prefix
        db_uri = db_uri.replace("postgres://", "postgresql+psycopg2://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        app.logger.warning("⚠️ Updated DB URI prefix to postgresql+psycopg2://")

    safe_uri = db_uri
    if "@" in db_uri and "://" in db_uri:  # Mask password in logs
        try:
            scheme, rest = db_uri.split("://", 1)
            if ":" in rest.split("@", 1)[0]:
                user_pass, host_part = rest.split("@", 1)
                user = user_pass.split(":")[0]
                safe_uri = f"{scheme}://{user}:****@{host_part}"
        except Exception:
            safe_uri = db_uri

    app.logger.info("🔗 Database URI (masked): %s", safe_uri)


def _initialize_extensions(app: Flask) -> None:
    """Initialize extensions (DB, migrations, etc.)."""
    init_extensions(app)

    auto_create = app.config.get("AUTO_CREATE_TABLES", os.getenv("AUTO_CREATE_TABLES", "false"))
    if str(auto_create).lower() in ("1", "true", "yes"):
        with app.app_context():
            db.create_all()
            app.logger.info("📦 Auto-created DB tables")


def _check_database_connection(app: Flask) -> None:
    """Verify DB connectivity at startup."""
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
        app.logger.info("✅ Database connection successful")
    except Exception as e:
        app.logger.critical("❌ Database connection failed: %s", e, exc_info=True)


def _configure_cors(app: Flask) -> None:
    """Enable CORS for Netlify + local dev frontends."""
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://aibudgettracker.netlify.app",
    ]

    allowed_origins = app.config.get("FRONTEND_URLS") or os.getenv("FRONTEND_URLS")
    if isinstance(allowed_origins, str):
        allowed_origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

    if not allowed_origins:
        allowed_origins = default_origins

    allowed_origins = sorted(set(allowed_origins + default_origins))

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Authorization"],
    )

    app.logger.info("🌍 CORS enabled for origins: %s", ", ".join(allowed_origins))


def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(expense_bp, url_prefix="/expenses")
    app.register_blueprint(salary_bp, url_prefix="/salaries")
    app.register_blueprint(trends_bp, url_prefix="/trends")
    app.register_blueprint(home_bp, url_prefix="/")

    app.logger.info("🧩 Blueprints registered: %s", list(app.blueprints.keys()))


def _register_error_handlers(app: Flask) -> None:
    """Global error handlers with consistent JSON output."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"status": "error", "message": e.description}), e.code
        app.logger.error("❌ Unhandled Exception", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def _configure_scheduler(app: Flask) -> None:
    """Configure APScheduler and load jobs."""
    try:
        scheduler = BackgroundScheduler()
        register_jobs(scheduler, app)
        scheduler.start()
        app.logger.info("⏰ Scheduler started successfully")
    except Exception as e:
        app.logger.exception("⚠️ Failed to start scheduler: %s", e)


# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    env = os.getenv("APP_ENV", "development").lower()

    config_class = {
        "production": ProductionConfig,
        "testing": TestingConfig,
        "development": DevelopmentConfig,
    }.get(env, DevelopmentConfig)

    app = create_app(config_class)

    host = app.config.get("FLASK_RUN_HOST", os.getenv("FLASK_RUN_HOST", "0.0.0.0"))
    port = int(app.config.get("FLASK_RUN_PORT", os.getenv("FLASK_RUN_PORT", 5000)))

    debug_config = app.config.get("FLASK_DEBUG")
    debug = (
        debug_config
        if isinstance(debug_config, bool)
        else str(debug_config or os.getenv("FLASK_DEBUG", "true")).lower() in ("1", "true", "yes")
    )

    try:
        app.logger.info(
            "🚀 Starting Budget Tracker API at http://%s:%s (debug=%s)", host, port, debug
        )
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        app.logger.info("👋 Budget Tracker API shutting down gracefully...")
