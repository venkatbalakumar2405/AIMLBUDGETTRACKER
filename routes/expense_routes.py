# routes/expense_routes.py
from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.expense import Expense
from models.salary import Salary   # ✅ integrate salary
from datetime import datetime

expense_bp = Blueprint("expense_bp", __name__)

# =====================================================
# ➤ Expense Summary + Salary Comparison
# =====================================================
@expense_bp.route("/expenses/summary/<int:user_id>", methods=["GET"])
def expense_summary(user_id):
    year = request.args.get("year", type=int, default=datetime.utcnow().year)

    # -------- Expenses --------
    expenses = (
        Expense.query.filter_by(user_id=user_id)
        .filter(db.extract("year", Expense.date) == year)
        .all()
    )

    category_totals = {}
    monthly_expenses = {m: 0 for m in range(1, 13)}

    for e in expenses:
        category = e.category or "Miscellaneous"
        category_totals[category] = category_totals.get(category, 0) + e.amount
        monthly_expenses[e.date.month] += e.amount

    # -------- Salary --------
    salaries = (
        Salary.query.filter_by(user_id=user_id)
        .filter(db.extract("year", Salary.date) == year)
        .all()
    )

    monthly_salary = {m: 0 for m in range(1, 13)}
    for s in salaries:
        monthly_salary[s.date.month] += s.amount

    # -------- Combine for Line Chart --------
    line_data = []
    for m in range(1, 13):
        line_data.append({
            "month": m,
            "salary": monthly_salary[m],
            "expenses": monthly_expenses[m],
        })

    return jsonify({
        "year": year,
        "total_expenses": sum(monthly_expenses.values()),
        "total_salary": sum(monthly_salary.values()),
        "category_totals": category_totals,
        "monthly_expenses": monthly_expenses,
        "monthly_salary": monthly_salary,
        "line_data": line_data   # ✅ directly usable for frontend charts
    }), 200
