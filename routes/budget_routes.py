from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.user import User
from models.expense import Expense
from sqlalchemy import func

budget_bp = Blueprint("budget", __name__)

# 📊 Expense Trends Endpoint (per expense timeline + summary)
@budget_bp.route("/trends", methods=["GET"])
def expense_trends():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    salary = user.salary or 0

    # ✅ Fetch all expenses for this user
    expenses = (
        Expense.query
        .filter_by(user_id=user.id)
        .order_by(Expense.date.asc())
        .all()
    )

    total_expenses = sum(e.amount for e in expenses)
    savings = salary - total_expenses

    # ✅ Format expenses with date
    expense_list = [
        {
            "id": e.id,
            "description": e.description,
            "amount": float(e.amount),
            "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None
        }
        for e in expenses
    ]

    return jsonify({
        "salary": float(salary),
        "total_expenses": float(total_expenses),
        "savings": float(savings if savings > 0 else 0),
        "expenses": expense_list
    })
