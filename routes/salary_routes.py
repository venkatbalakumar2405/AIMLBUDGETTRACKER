from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.salary import Salary
from datetime import datetime

salary_bp = Blueprint("salary", __name__)

@salary_bp.route("/salary", methods=["POST"])
def add_salary():
    data = request.get_json()
    try:
        salary = Salary(
            user_id=data["user_id"],
            amount=data["amount"],
            salary_date=datetime.strptime(data["salary_date"], "%Y-%m-%d")
        )
        db.session.add(salary)
        db.session.commit()
        return jsonify({"message": "Salary added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400