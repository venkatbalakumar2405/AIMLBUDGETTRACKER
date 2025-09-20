from flask import Blueprint, request, jsonify, current_app
from models.expense import Expense
from utils.extensions import db
from datetime import datetime
from routes.auth_routes import token_required  # ✅ Import token_required

budget_bp = Blueprint("budget", __name__)


# ================== Helper Functions ==================

def clean_amount(value):
    """Convert string/number to float safely (removes ₹, commas)."""
    if value is None:
        return None
    try:
        return float(str(value).replace("₹", "").replace(",", "").strip())
    except ValueError:
        return None


def parse_date(date_str):
    """Parse date string or return current UTC datetime."""
    if not date_str:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def build_summary(user, expenses):
    """Build balance summary and category breakdown."""
    salary = float(user.salary or 0)
    budget_limit = float(user.budget_limit or 0)

    total_expenses = sum(float(e.amount) for e in expenses)
    savings = salary - total_expenses if salary > 0 else 0
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None

    # ✅ Category breakdown
    category_summary = {}
    for e in expenses:
        cat = (e.category or "Miscellaneous").title()
        category_summary[cat] = category_summary.get(cat, 0) + float(e.amount)

    return {
        "salary": salary,
        "budget_limit": budget_limit,
        "total_expenses": total_expenses,
        "savings": savings,
        "usage_percent": round(usage_percent, 2) if usage_percent else None,
        "category_summary": category_summary,
    }


# ================== Expenses ==================

@budget_bp.route("/expenses", methods=["GET"])
@token_required
def get_expenses(current_user):
    """Fetch all expenses for the logged-in user with basic summary."""
    try:
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()

        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                "category": e.category or "Miscellaneous",
            }
            for e in expenses
        ]

        return jsonify({
            "data": expense_list,
            "summary": build_summary(current_user, expenses)
        }), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /budget/expenses: {e}")
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/add", methods=["POST"])
@token_required
def add_expense(current_user):
    """Add a new expense for the logged-in user and return updated summary."""
    try:
        data = request.get_json() or {}
        description = data.get("description", "")
        amount = clean_amount(data.get("amount"))
        category = (data.get("category") or "Miscellaneous").title()
        date = parse_date(data.get("date"))

        if amount is None:
            return jsonify({"error": "Valid amount is required"}), 400
        if not date:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        new_expense = Expense(
            user_id=current_user.id,
            description=description,
            amount=amount,
            date=date,
            category=category,
        )
        db.session.add(new_expense)
        db.session.commit()

        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        summary = build_summary(current_user, expenses)

        response = {
            "message": "Expense added successfully",
            "summary": summary
        }
        if summary["budget_limit"] > 0 and summary["total_expenses"] > summary["budget_limit"]:
            response["warning"] = "⚠️ You have exceeded your budget limit!"

        return jsonify(response), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/add: {e}")
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
@token_required
def update_expense(current_user, id):
    """Update an existing expense by ID (only if it belongs to the user)."""
    try:
        data = request.get_json() or {}
        expense = Expense.query.filter_by(id=id, user_id=current_user.id).first()
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        if "description" in data:
            expense.description = data["description"]
        if "amount" in data:
            new_amount = clean_amount(data["amount"])
            if new_amount is None:
                return jsonify({"error": "Amount must be a valid number"}), 400
            expense.amount = new_amount
        if "category" in data:
            expense.category = (data["category"] or "Miscellaneous").title()

        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/update: {e}")
        return jsonify({"error": "Server error while updating expense"}), 500


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
@token_required
def delete_expense(current_user, id):
    """Delete an expense by ID (only if it belongs to the user)."""
    try:
        expense = Expense.query.filter_by(id=id, user_id=current_user.id).first()
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/delete: {e}")
        return jsonify({"error": "Server error while deleting expense"}), 500


# ================== Budget Settings ==================

@budget_bp.route("/set-budget", methods=["PUT"])
@token_required
def set_budget(current_user):
    """Update budget limit for the logged-in user."""
    try:
        data = request.get_json() or {}
        budget_limit = clean_amount(data.get("budget_limit"))

        if budget_limit is None:
            return jsonify({"error": "Valid budget_limit is required"}), 400

        current_user.budget_limit = budget_limit
        db.session.commit()

        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        summary = build_summary(current_user, expenses)

        return jsonify({
            "message": "Budget limit updated successfully",
            "summary": summary
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /budget/set-budget: {e}")
        return jsonify({"error": "Server error while setting budget"}), 500


# ================== Trends ==================

@budget_bp.route("/trends", methods=["GET"])
@token_required
def get_trends(current_user):
    """Get expense trends for line chart & pie chart data."""
    try:
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date).all()
        summary = build_summary(current_user, expenses)

        expense_list = [
            {
                "date": e.date.strftime("%Y-%m-%d"),
                "amount": float(e.amount),
                "category": e.category or "Miscellaneous",
            }
            for e in expenses
        ]

        return jsonify({
            "summary": summary,
            "expenses": expense_list,          # For line chart (trend over time)
            "category_summary": summary["category_summary"],  # For pie chart
        }), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /budget/trends: {e}")
        return jsonify({"error": "Server error while fetching trends"}), 500