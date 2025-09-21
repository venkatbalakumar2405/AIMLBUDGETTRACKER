from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from utils.extensions import db
from models.expense import Expense
from utils.decorators import token_required

# ================== Blueprint Setup ================== #
expense_bp = Blueprint("expenses", __name__)
# ⚠️ No per-blueprint CORS here (handled globally in app.py)


# ================== ROUTES ================== #
@expense_bp.route("/", methods=["POST"])
@token_required
def add_expense(current_user):
    """Add a new expense for the logged-in user."""
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required = ["category", "amount", "expense_date"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        expense = Expense(
            user_id=current_user.id,
            category=data["category"].strip(),
            amount=float(data["amount"]),
            date=datetime.strptime(data["expense_date"], "%Y-%m-%d"),
        )

        db.session.add(expense)
        db.session.commit()

        current_app.logger.info("✅ Expense added for user %s", current_user.email)
        return jsonify({
            "message": "Expense added successfully",
            "expense": {
                "id": expense.id,
                "category": expense.category,
                "amount": float(expense.amount),
                "date": expense.date.strftime("%Y-%m-%d"),
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Error in /expenses [POST]: %s", e)
        return jsonify({"error": "Failed to add expense"}), 500
