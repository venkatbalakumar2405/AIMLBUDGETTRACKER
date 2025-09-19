import os
import sys
import io
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from utils.extensions import db, migrate, mail, scheduler

# Import models for SQLAlchemy (needed for migrations & Alembic autogenerate)
from models.user import User  # noqa: F401
from models.expense import Expense  # noqa: F401

# Import blueprints
from routes.budget_routes import budget_bp
from routes.home_routes import home_bp
from routes.auth_routes import auth_bp

# ✅ Force UTF-8 for stdout/stderr (fixes Windows console emoji crash)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def create_app(config_class: type[Config] = Config) -> Flask:
    """Application factory for the Budget Tracker API."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---------------- CONFIGURE APP ---------------- #
    _configure_logging(app)
    _log_database_uri(app)   # ✅ new (with fail-fast)
    _initialize_extensions(app)
    _configure_cors(app)
    _register_blueprints(app)
    _register_health_check(app)
    _register_error_handlers(app)
    _configure_scheduler(app)

    return app


# ---------------- HELPERS ---------------- #

def _configure_logging(app: Flask) -> None:
    """Configure logging format and level with file rotation."""
    log_level = logging.DEBUG if app.debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(level=log_level, format=log_format)
    app.logger.setLevel(log_level)

    # Logs directory comes from config (default: ./logs)
    log_dir = app.config.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # File logging (rotating 5 MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, app.config.get("LOG_FILE", "budget_tracker.log")),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"  # ✅ ensure UTF-8 in log file too
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)

    app.logger.info("📝 Logging configured (level=%s)", logging.getLevelName(log_level))


def _log_database_uri(app: Flask) -> None:
    """Log database URI safely (mask password & fix old postgres:// format)."""
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

    if not db_uri:
        app.logger.critical("❌ No SQLALCHEMY_DATABASE_URI configured. Exiting...")
        sys.exit(1)   # 🚨 Exit immediately

    # Fix old postgres:// scheme (SQLAlchemy 2.x requires postgresql://)
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        app.logger.warning("⚠️ Updated DB URI prefix from postgres:// to postgresql://")

    # Mask password
    safe_uri = db_uri
    if "@" in db_uri and "://" in db_uri:
        try:
            scheme, rest = db_uri.split("://", 1)
            if ":" in rest.split("@", 1)[0]:  # has user:pass@
                user_pass, host_part = rest.split("@", 1)
                user = user_pass.split(":")[0]
                safe_uri = f"{scheme}://{user}:****@{host_part}"
        except Exception:
            pass

    app.logger.info("🔗 Database URI: %s", safe_uri)


def _initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions (DB, migrations, mail, etc.)."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    if app.config.get("AUTO_CREATE_TABLES", False):
        with app.app_context():
            db.create_all()
            app.logger.info("📦 Database tables auto-created")


def _configure_cors(app: Flask) -> None:
    """Configure CORS safely using Flask-CORS."""
    allowed_origins: list[str] = app.config.get("FRONTEND_URLS", ["http://localhost:5173"])

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.logger.info("🌍 CORS enabled for origins: %s", ", ".join(allowed_origins))


def _register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(home_bp)

    app.logger.info("🧩 Blueprints registered: %s", list(app.blueprints.keys()))


def _register_health_check(app: Flask) -> None:
    """Register health check endpoint."""
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200


def _register_error_handlers(app: Flask) -> None:
    """Global error handler for HTTP and unexpected exceptions."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        app.logger.error("❌ Unhandled Exception", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def _configure_scheduler(app: Flask) -> None:
    """Initialize APScheduler with safe context for jobs."""
    try:
        scheduler.init_app(app)
        scheduler.start()

        @scheduler.task("cron", id="daily_expense_check", hour=0, minute=0)
        def daily_task():
            with app.app_context():
                app.logger.info("🕛 Daily job executed: checking expenses...")

        app.logger.info("⏰ Scheduler started successfully")
    except Exception as e:
        app.logger.exception("⚠️ Failed to start scheduler: %s", e)


# ---------------- ENTRY POINT ---------------- #

if __name__ == "__main__":
    app = create_app()
    host = app.config.get("FLASK_RUN_HOST", "0.0.0.0")
    port = app.config.get("FLASK_RUN_PORT", 5000)
    debug = app.config.get("FLASK_DEBUG", True)

    try:
        app.logger.info("🚀 Starting Budget Tracker API at http://%s:%s (debug=%s)", host, port, debug)
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        app.logger.info("👋 Budget Tracker API shutting down gracefully...")