from flask import Blueprint, jsonify
from models.user import User
from models.expense import Expense

trends_bp = Blueprint("trends", __name__)

@trends_bp.route("/<string:email>", methods=["GET"])
def get_expense_trends(email: str):
    """Return expense trends (grouped by category & monthly) for a given user email."""
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch all expenses for the user
    expenses = Expense.query.filter_by(user_id=user.id).all()

    # Aggregate by category
    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0) + exp.amount

    # Aggregate by month
    monthly_totals = {}
    for exp in expenses:
        month = exp.date.strftime("%Y-%m") if exp.date else "Unknown"
        monthly_totals[month] = monthly_totals.get(month, 0) + exp.amount

    return jsonify({
        "category_trends": category_totals,
        "monthly_trends": monthly_totals,
    }), 200