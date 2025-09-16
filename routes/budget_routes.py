from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.user import User, Expense
from sqlalchemy import extract

budget_bp = Blueprint("budget", __name__)

# ============================
# Monthly aggregated trends
# ============================
@budget_bp.route("/monthly-trends", methods=["GET"])
def monthly_trends():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get all expenses for the user
    expenses = (
        db.session.query(
            extract("year", Expense.date).label("year"),
            extract("month", Expense.date).label("month"),
            db.func.sum(Expense.amount).label("total_expenses"),
        )
        .filter(Expense.user_id == user.id)
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    # Format monthly results
    results = []
    for year, month, total_expenses in expenses:
        savings = user.salary - total_expenses if user.salary else 0
        results.append({
            "month": f"{int(month):02d}-{int(year)}",  # e.g. 09-2025
            "salary": user.salary,
            "total_expenses": float(total_expenses),
            "savings": float(savings),
        })

    return jsonify({"monthly_trends": results})