from flask import Blueprint, jsonify, current_app
from collections import defaultdict

from models.expense import Expense
from utils.decorators import token_required

# ================== Blueprint Setup ================== #
trends_bp = Blueprint("trends", __name__)
# ⚠️ No per-blueprint CORS (handled globally in app.py)


# ================== ROUTES ================== #
@trends_bp.route("/", methods=["GET"])
@token_required
def get_expense_trends(current_user):
    """
    Return expense trends for the logged-in user:
      - category_trends: total spent per category
      - monthly_trends: total spent per month (YYYY-MM)
    """
    try:
        # Fetch all expenses for the user
        expenses = Expense.query.filter_by(user_id=current_user.id).all()

        # Aggregate by category
        category_totals = defaultdict(float)
        for exp in expenses:
            category = exp.category or "Miscellaneous"
            category_totals[category] += float(exp.amount or 0)

        # Aggregate by month
        monthly_totals = defaultdict(float)
        for exp in expenses:
            if exp.date:
                month = exp.date.strftime("%Y-%m")
            else:
                month = "Unknown"
            monthly_totals[month] += float(exp.amount or 0)

        return jsonify({
            "email": current_user.email,
            "category_trends": dict(category_totals),
            "monthly_trends": dict(monthly_totals),
        }), 200

    except Exception as e:
        current_app.logger.exception("❌ Error in /trends [GET]: %s", e)
        return jsonify({"error": "Failed to fetch expense trends"}), 500