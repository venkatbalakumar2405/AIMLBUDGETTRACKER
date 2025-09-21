import os
import sys
import io
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

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

# ✅ Ensure UTF-8 logs (Windows fix for emoji / stdout crashes)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# ---------------- APP FACTORY ---------------- #
def create_app(config_class: type[Config] = Config) -> Flask:
    """Application factory for Budget Tracker API."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    _configure_logging(app)
    _log_database_uri(app)
    _initialize_extensions(app)
    _configure_cors(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_scheduler(app)

    return app


# ---------------- HELPERS ---------------- #
def _configure_logging(app: Flask) -> None:
    """Configure logging with rotation and console output."""
    log_level = logging.DEBUG if app.debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

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


def _log_database_uri(app: Flask) -> None:
    """Mask DB password & fix old postgres:// format for SQLAlchemy."""
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", ""))

    if not db_uri:
        app.logger.critical("❌ No SQLALCHEMY_DATABASE_URI configured. Exiting...")
        sys.exit(1)

    # Fix deprecated postgres:// prefix
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        app.logger.warning("⚠️ Updated DB URI prefix to postgresql://")

    # Mask password for logs
    safe_uri = db_uri
    if "@" in db_uri and "://" in db_uri:
        try:
            scheme, rest = db_uri.split("://", 1)
            if ":" in rest.split("@", 1)[0]:
                user_pass, host_part = rest.split("@", 1)
                user = user_pass.split(":")[0]
                safe_uri = f"{scheme}://{user}:****@{host_part}"
        except Exception:
            pass

    app.logger.info("🔗 Database URI: %s", safe_uri)


def _initialize_extensions(app: Flask) -> None:
    """Initialize extensions (DB, migrations, mail)."""
    init_extensions(app)

    auto_create = app.config.get(
        "AUTO_CREATE_TABLES", os.getenv("AUTO_CREATE_TABLES", "false")
    )
    if str(auto_create).lower() in ("1", "true", "yes"):
        with app.app_context():
            db.create_all()
            app.logger.info("📦 Auto-created DB tables")


def _configure_cors(app: Flask) -> None:
    """Enable strict CORS for frontend apps."""
    # Default safe origins
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://aibudgettracker.netlify.app",  # ✅ Netlify frontend
    ]

    # Load from config or env
    allowed_origins = app.config.get("FRONTEND_URLS") or os.getenv("FRONTEND_URLS")
    if isinstance(allowed_origins, str):
        allowed_origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]
    if not allowed_origins:
        allowed_origins = default_origins

    # Final deduplicated list
    allowed_origins = list(set(allowed_origins + default_origins))

    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Authorization"],
    )

    app.logger.info("🌍 CORS enabled for: %s", ", ".join(allowed_origins))


def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(expense_bp, url_prefix="/expenses")
    app.register_blueprint(salary_bp, url_prefix="/salaries")
    app.register_blueprint(trends_bp, url_prefix="/trends")
    app.register_blueprint(home_bp, url_prefix="/")  # ✅ heartbeat route

    app.logger.info("🧩 Blueprints registered: %s", list(app.blueprints.keys()))


def _register_error_handlers(app: Flask) -> None:
    """Global error handlers."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        app.logger.error("❌ Unhandled Exception", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def _configure_scheduler(app: Flask) -> None:
    """Configure APScheduler and load jobs."""
    try:
        scheduler = BackgroundScheduler()
        register_jobs(scheduler, app)  # ✅ pass app into job registration
        scheduler.start()
        app.logger.info("⏰ Scheduler started successfully")
    except Exception as e:
        app.logger.exception("⚠️ Failed to start scheduler: %s", e)


# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    env = os.getenv("APP_ENV", "development").lower()

    if env == "production":
        config_class = ProductionConfig
    elif env == "testing":
        config_class = TestingConfig
    else:
        config_class = DevelopmentConfig

    app = create_app(config_class)

    host = app.config.get("FLASK_RUN_HOST", os.getenv("FLASK_RUN_HOST", "0.0.0.0"))
    port = int(app.config.get("FLASK_RUN_PORT", os.getenv("FLASK_RUN_PORT", 5000)))

    debug_config = app.config.get("FLASK_DEBUG")
    if isinstance(debug_config, bool):
        debug = debug_config
    else:
        debug = str(debug_config or os.getenv("FLASK_DEBUG", "true")).lower() in (
            "1",
            "true",
            "yes",
        )

    try:
        app.logger.info(
            "🚀 Starting Budget Tracker API at http://%s:%s (debug=%s)", host, port, debug
        )
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        app.logger.info("👋 Budget Tracker API shutting down gracefully...")