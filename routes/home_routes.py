from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from models import User, Expense
from routes.budget_routes import build_summary  # still needs explicit import

home_bp = Blueprint("home", __name__)

# ================== API Metadata ==================
API_NAME = "Budget Tracker API"
API_VERSION = "1.0.0"


# ================== Root Endpoint ==================
@home_bp.route("/", methods=["GET"])
def home():
    """
    Root API endpoint - returns service info.
    If ?email=<user_email> is provided, includes budget summary.
    """
    email: str | None = request.args.get("email")
    response: dict = {
        "message": f"Welcome to the {API_NAME} 🚀",
        "status": "running",
        "version": API_VERSION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    if email:
        user = User.query.filter_by(email=email.lower().strip()).first()
        if user:
            expenses = Expense.query.filter_by(user_id=user.id).all()
            try:
                response["summary"] = build_summary(user, expenses)
            except Exception as e:
                current_app.logger.error(f"Summary generation failed: {e}")
                response["summary_error"] = f"Failed to generate summary: {str(e)}"
        else:
            response["user_error"] = f"No user found with email: {email}"

    return jsonify(response), 200


# ================== Health Check ==================
@home_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "uptime": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "version": API_VERSION,
    }), 200


# ================== API Metadata ==================
@home_bp.route("/info", methods=["GET"])
def api_info():
    """API metadata and available endpoints."""
    endpoints = {}
    for rule in home_bp.url_map.iter_rules():
        if rule.endpoint != "static":
            endpoints[rule.endpoint] = str(rule)

    return jsonify({
        "api": API_NAME,
        "version": API_VERSION,
        "status": "running",
        "endpoints": endpoints,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }), 200