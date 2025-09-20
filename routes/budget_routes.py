from flask import Blueprint, request, jsonify, current_app
from models.expense import Expense
from models.salary import Salary
from utils.extensions import db
from utils.decorators import token_required   # ✅ fixed import
from datetime import datetime

budget_bp = Blueprint("budget", __name__)


# ================== Helpers ==================
def clean_amount(value):
    """Convert amount safely to float, return None if invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date(value):
    """Parse YYYY-MM-DD into datetime.date, return None if invalid."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def build_summary(user, expenses):
    """Build budget summary including salary history + categories."""

    # Get all salaries (latest first)
    salaries = (
        Salary.query.filter_by(user_id=user.id)
        .order_by(Salary.salary_date.desc())
        .all()
    )
    salary_history = [
        {
            "id": s.id,
            "amount": float(s.amount),
            "salary_date": s.salary_date.strftime("%Y-%m-%d")
            if s.salary_date
            else None,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if s.created_at
            else None,
        }
        for s in salaries
    ]

    # Latest salary if available
    salary = float(salaries[0].amount) if salaries else 0.0
    budget_limit = float(getattr(user, "budget_limit", 0) or 0)

    total_expenses = sum(float(e.amount) for e in expenses)
    savings = salary - total_expenses if salary > 0 else 0
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None

    # Category breakdown
    category_summary = {}
    for e in expenses:
        cat = (e.category or "Miscellaneous").title()
        category_summary[cat] = category_summary.get(cat, 0) + float(e.amount)

    return {
        "salary": salary,
        "salary_history": salary_history,
        "budget_limit": budget_limit,
        "total_expenses": total_expenses,
        "savings": savings,
        "usage_percent": round(usage_percent, 2) if usage_percent else None,
        "category_summary": category_summary,
    }


# ================== Routes ==================
@budget_bp.route("/expenses", methods=["GET"])
@token_required
def get_expenses(current_user):
    """Fetch expenses + summary for the logged-in user."""
    try:
        expenses = (
            Expense.query.filter_by(user_id=current_user.id)
            .order_by(Expense.expense_date.desc())
            .all()
        )

        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.expense_date.strftime("%Y-%m-%d") if e.expense_date else None,
                "category": e.category,
            }
            for e in expenses
        ]

        summary = build_summary(current_user, expenses)
        return jsonify({"data": expense_list, "summary": summary}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /budget/expenses: {e}")
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/expenses/add", methods=["POST"])
@token_required
def add_expense(current_user):
    """Add a new expense for the logged-in user."""
    try:
        data = request.get_json() or {}
        amount = clean_amount(data.get("amount"))
        expense_date = parse_date(data.get("expense_date"))
        category = data.get("category") or "Miscellaneous"
        description = data.get("description")

        if amount is None:
            return jsonify({"error": "Valid amount is required"}), 400
        if not expense_date:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        new_expense = Expense(
            user_id=current_user.id,
            amount=amount,
            category=category,
            description=description,
            expense_date=expense_date,
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/expenses/add: {e}")
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/expenses/delete/<int:id>", methods=["DELETE"])
@token_required
def delete_expense(current_user, id):
    """Delete an expense record if it belongs to the user."""
    try:
        expense = Expense.query.filter_by(id=id, user_id=current_user.id).first()
        if not expense:
            return jsonify({"error": "Expense record not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/expenses/delete: {e}")
        return jsonify({"error": "Server error while deleting expense"}), 500