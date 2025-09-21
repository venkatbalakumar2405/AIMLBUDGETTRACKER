from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.expense import Expense
from datetime import datetime

expense_bp = Blueprint("expense", __name__)

@expense_bp.route("/expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    try:
        expense = Expense(
            user_id=data["user_id"],
            category=data["category"],
            amount=data["amount"],
            expense_date=datetime.strptime(data["expense_date"], "%Y-%m-%d")
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400