from flask import Flask, jsonify
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

    # ✅ CORS setup
    if app.config.get("ENV") == "production":
        allowed_origins = [
            "https://myapp.com",  # 🔒 production frontend
        ]
    else:
        allowed_origins = [
            "http://localhost:5173",  # vite default
            "http://localhost:5176",  # your case
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5176",
        ]

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
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

    # ✅ More precise error handling
    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)