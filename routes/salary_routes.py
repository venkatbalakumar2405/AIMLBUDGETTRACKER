from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from utils.extensions import db
from models.salary import Salary
from utils.decorators import token_required

# ================== Blueprint Setup ================== #
salary_bp = Blueprint("salaries", __name__)
# ⚠️ No per-blueprint CORS (handled globally in app.py)


# ================== ROUTES ================== #
@salary_bp.route("/", methods=["POST"])
@token_required
def add_salary(current_user):
    """Add a new salary entry for the logged-in user."""
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required = ["amount", "salary_date"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        salary = Salary(
            user_id=current_user.id,
            amount=float(data["amount"]),
            salary_date=datetime.strptime(data["salary_date"], "%Y-%m-%d"),
        )

        db.session.add(salary)
        db.session.commit()

        current_app.logger.info("✅ Salary added for user %s", current_user.email)
        return jsonify({
            "message": "Salary added successfully",
            "salary": {
                "id": salary.id,
                "amount": float(salary.amount),
                "salary_date": salary.salary_date.strftime("%Y-%m-%d"),
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Error in /salaries [POST]: %s", e)
        return jsonify({"error": "Failed to add salary"}), 500