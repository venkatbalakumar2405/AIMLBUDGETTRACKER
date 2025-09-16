from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.user import User
from models.expense import Expense
from sqlalchemy import extract, func
from datetime import datetime

budget_bp = Blueprint("budget", __name__)

# ============================
# 🔹 Get Monthly Expense Trends
# ============================
@budget_bp.route("/monthly-trends", methods=["GET"])
def monthly_trends():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ✅ Group expenses by year & month
    expenses = (
        db.session.query(
            extract("year", Expense.date).label("year"),
            extract("month", Expense.date).label("month"),
            func.sum(Expense.amount).label("total_expenses"),
        )
        .filter(Expense.user_id == user.id)
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    # ✅ Build trends (always include salary & savings)
    trends = []
    for e in expenses:
        salary = user.salary or 0
        total_expenses = float(e.total_expenses or 0)
        savings = salary - total_expenses

        trends.append({
            "year": int(e.year),
            "month": f"{int(e.month):02d}",
            "salary": salary,
            "expenses": total_expenses,
            "savings": savings if savings > 0 else 0
        })

    # ✅ If no expenses, still return at least current month with salary
    if not trends:
        now = datetime.now()
        trends.append({
            "year": now.year,
            "month": f"{now.month:02d}",
            "salary": user.salary or 0,
            "expenses": 0,
            "savings": user.salary or 0
        })

    return jsonify({"monthly_trends": trends})