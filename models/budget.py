from flask import Blueprint, request, jsonify
from models.user import User
from models.expense import Expense
from utils.extensions import db
from datetime import datetime

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
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def calculate_budget_usage(user_id, budget_limit):
    """Calculate total expenses and budget usage percentage."""
    total_expenses = (
        db.session.query(db.func.sum(Expense.amount))
        .filter_by(user_id=user_id)
        .scalar()
        or 0
    )
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None
    return float(total_expenses), round(usage_percent, 2) if usage_percent else None


# ================== Expenses ==================

@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = (
            Expense.query.filter_by(user_id=user.id)
            .order_by(Expense.date.desc())
            .all()
        )

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

        return jsonify({"data": expense_list}), 200
    except Exception as e:
        print("❌ Error in /budget/expenses:", str(e))
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/add", methods=["POST"])
def add_expense():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        description = data.get("description", "")
        amount = clean_amount(data.get("amount"))
        category = data.get("category", "Miscellaneous")
        date = parse_date(data.get("date"))

        if not email or amount is None:
            return jsonify({"error": "Email and valid amount are required"}), 400
        if not date:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_expense = Expense(
            user_id=user.id,
            description=description,
            amount=amount,
            date=date,
            category=category,
        )
        db.session.add(new_expense)
        db.session.commit()

        # ✅ Calculate updated budget usage
        total_expenses, usage_percent = calculate_budget_usage(user.id, user.budget_limit)
        warning = None
        if user.budget_limit > 0 and total_expenses > user.budget_limit:
            warning = "⚠️ You have exceeded your budget limit!"

        response = {
            "message": "Expense added successfully",
            "total_expenses": total_expenses,
            "budget_limit": float(user.budget_limit or 0),
            "usage_percent": usage_percent,
        }
        if warning:
            response["warning"] = warning

        return jsonify(response), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/add:", str(e))
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    try:
        data = request.get_json() or {}
        expense = Expense.query.get(id)
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
            expense.category = data["category"]

        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/update:", str(e))
        return jsonify({"error": "Server error while updating expense"}), 500


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    try:
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/delete:", str(e))
        return jsonify({"error": "Server error while deleting expense"}), 500


# ================== Budget Settings ==================

@budget_bp.route("/set-budget", methods=["PUT"])
def set_budget():
    """Update user budget limit (danger line)."""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        budget_limit = clean_amount(data.get("budget_limit"))

        if not email or budget_limit is None:
            return jsonify({"error": "Email and valid budget_limit are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.budget_limit = budget_limit
        db.session.commit()

        return jsonify({
            "message": "Budget limit updated successfully",
            "budget_limit": user.budget_limit,
        }), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/set-budget:", str(e))
        return jsonify({"error": "Server error while setting budget"}), 500


# ================== Trends ==================

@budget_bp.route("/trends", methods=["GET"])
def get_trends():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = (
            Expense.query.filter_by(user_id=user.id)
            .order_by(Expense.date)
            .all()
        )

        total_expenses = sum(e.amount for e in expenses)
        salary = user.salary or 0
        savings = salary - total_expenses if salary > 0 else 0
        budget_limit = user.budget_limit or 0
        usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None

        expense_list = [
            {
                "date": e.date.strftime("%Y-%m-%d"),
                "amount": float(e.amount),
                "category": e.category or "Miscellaneous",
            }
            for e in expenses
        ]

        # ✅ Category-wise breakdown
        category_summary = {}
        for e in expenses:
            category_summary[e.category] = category_summary.get(e.category, 0) + float(e.amount)

        return jsonify({
            "salary": float(salary),
            "budget_limit": float(budget_limit),
            "total_expenses": float(total_expenses),
            "savings": float(savings),
            "usage_percent": round(usage_percent, 2) if usage_percent else None,
            "expenses": expense_list,
            "category_summary": category_summary,
        }), 200
    except Exception as e:
        print("❌ Error in /budget/trends:", str(e))
        return jsonify({"error": "Server error while fetching trends"}), 500