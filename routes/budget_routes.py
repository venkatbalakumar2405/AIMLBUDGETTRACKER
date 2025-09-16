from flask import Blueprint, request, jsonify
from models.user import User
from models.expense import Expense
from utils.extensions import db
from datetime import datetime

budget_bp = Blueprint("budget", __name__)

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

        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc()).all()

        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                "category": e.category or "Miscellaneous"
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
        data = request.get_json()
        email = data.get("email")
        description = data.get("description", "")
        amount = data.get("amount")
        category = data.get("category", "Miscellaneous")
        date_str = data.get("date")

        if not email or amount is None:
            return jsonify({"error": "Email and amount are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # ✅ Clean amount (remove ₹ and commas)
        try:
            clean_amount = float(str(amount).replace("₹", "").replace(",", "").strip())
        except ValueError:
            return jsonify({"error": "Amount must be a number"}), 400

        # ✅ Handle custom date
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            date = datetime.utcnow()

        new_expense = Expense(
            user_id=user.id,
            description=description,
            amount=clean_amount,
            date=date,
            category=category
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        print("❌ Error in /budget/add:", str(e))
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    try:
        data = request.get_json()
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        if "description" in data:
            expense.description = data["description"]
        if "amount" in data:
            try:
                expense.amount = float(str(data["amount"]).replace("₹", "").replace(",", "").strip())
            except ValueError:
                return jsonify({"error": "Amount must be a number"}), 400
        if "category" in data:
            expense.category = data["category"]

        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200
    except Exception as e:
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
        print("❌ Error in /budget/delete:", str(e))
        return jsonify({"error": "Server error while deleting expense"}), 500


# ================== Budget Settings ==================

@budget_bp.route("/set-budget", methods=["PUT"])
def set_budget():
    """Update user budget limit (danger line)."""
    try:
        data = request.get_json()
        email = data.get("email")
        budget_limit = data.get("budget_limit")

        if not email or budget_limit is None:
            return jsonify({"error": "Email and budget_limit are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.budget_limit = float(budget_limit)
        db.session.commit()

        return jsonify({"message": "Budget limit updated successfully", "budget_limit": user.budget_limit}), 200
    except Exception as e:
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

        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()

        total_expenses = sum(e.amount for e in expenses)
        salary = user.salary or 0
        savings = salary - total_expenses if salary > 0 else 0
        budget_limit = user.budget_limit or 0

        expense_list = [
            {
                "date": e.date.strftime("%Y-%m-%d"),
                "amount": float(e.amount),
                "category": e.category or "Miscellaneous"
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
            "expenses": expense_list,
            "category_summary": category_summary
        }), 200
    except Exception as e:
        print("❌ Error in /budget/trends:", str(e))
        return jsonify({"error": "Server error while fetching trends"}), 500