from flask import Blueprint, jsonify, request
from datetime import datetime
from models.user import User
from models.expense import Expense
from routes.budget_routes import build_summary  # ✅ absolute import

home_bp = Blueprint("home", __name__)

# ================== Root Endpoint ==================
@home_bp.route("/", methods=["GET"])
def home():
    """
    Root API endpoint - returns service info.
    If ?email=<user_email> is provided, includes budget summary.
    """
    email: str | None = request.args.get("email")
    response: dict = {
        "message": "Welcome to the Budget Tracker API 🚀",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    if email:
        user = User.query.filter_by(email=email.lower().strip()).first()
        if user:
            expenses = Expense.query.filter_by(user_id=user.id).all()
            try:
                response["summary"] = build_summary(user, expenses)
            except Exception as e:
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
        "version": "1.0.0",
    }), 200


# ================== API Metadata ==================
@home_bp.route("/info", methods=["GET"])
def api_info():
    """API metadata and available endpoints."""
    return jsonify({
        "api": "Budget Tracker API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "info": "/info",
            "expenses": "/budget/expenses",
            "add_expense": "/budget/add",
            "update_expense": "/budget/update/<id>",
            "delete_expense": "/budget/delete/<id>",
            "salary": "/budget/salary",
            "set_budget": "/budget/set-budget",
            "trends": "/budget/trends",
            "export_csv": "/budget/export/csv",
            "export_excel": "/budget/export/excel",
            "export_pdf": "/budget/export/pdf",
            "export_zip": "/budget/export/zip",
        },
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }), 200