from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.user import User
from models.expense import Expense

budget_bp = Blueprint("budget", __name__)

# ✅ Add expense
@budget_bp.route("/add", methods=["POST"])
def add_expense():
    data = request.get_json()
    email = data.get("email")
    amount = data.get("amount")
    description = data.get("description")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expense = Expense(amount=amount, description=description, user_id=user.id)
    db.session.add(expense)
    db.session.commit()

    return jsonify({"message": "Expense added successfully"}), 201


# ✅ Get all expenses for a user
@budget_bp.route("/all/<email>", methods=["GET"])
def get_expenses(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify([
        {"id": e.id, "amount": e.amount, "description": e.description}
        for e in expenses
    ])


# ✅ Update expense
@budget_bp.route("/update/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    expense.amount = data.get("amount", expense.amount)
    expense.description = data.get("description", expense.description)
    db.session.commit()

    return jsonify({"message": "Expense updated successfully"})


# ✅ Delete expense
@budget_bp.route("/delete/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted successfully"})


# ✅ Update salary
@budget_bp.route("/salary", methods=["PUT"])
def update_salary():
    data = request.get_json()
    email = data.get("email")
    salary = data.get("salary")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = salary
    db.session.commit()

    return jsonify({"message": "Salary updated successfully"})


# ✅ Reset all (clear salary + expenses)
@budget_bp.route("/reset", methods=["POST"])
def reset_data():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = 0
    Expense.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"message": "All data reset successfully"})