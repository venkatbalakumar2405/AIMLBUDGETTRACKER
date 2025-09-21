from flask import Blueprint, jsonify, current_app

from models.expense import Expense
from utils.decorators import token_required

# ================== Blueprint Setup ================== #
budget_bp = Blueprint("budget", __name__)
# ⚠️ Do NOT enable per-blueprint CORS here (handled globally in app.py)


# ================== HELPER ================== #
def build_summary(user, expenses):
    """Reusable helper: build summary for a user’s budget and expenses."""
    total_expenses = sum(float(exp.amount or 0) for exp in expenses)
    salary = float(user.salary or 0)
    budget_limit = float(user.budget_limit or 0)

    return {
        "salary": salary,
        "budget_limit": budget_limit,
        "total_expenses": total_expenses,
        "remaining_budget": max(budget_limit - total_expenses, 0),
        "expense_count": len(expenses),
    }


# ================== ROUTES ================== #
@budget_bp.route("/summary/<email>", methods=["GET"])
@token_required
def get_budget_summary(current_user, email: str):
    """Return budget summary for a given user (authorized)."""
    try:
        if current_user.email != email.lower().strip():
            return jsonify({"error": "Unauthorized access"}), 403

        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        summary = build_summary(current_user, expenses)

        return jsonify({
            "email": current_user.email,
            "summary": summary
        }), 200

    except Exception as e:
        current_app.logger.exception("❌ Error in /budget/summary/<email>: %s", e)
        return jsonify({"error": "Internal server error"}), 500
