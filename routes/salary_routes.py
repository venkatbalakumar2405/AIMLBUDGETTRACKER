from flask import Blueprint, request, jsonify, current_app
from models.salary import Salary
from utils.extensions import db
from routes.auth_routes import token_required  # ✅ Import token_required
from .budget_routes import clean_amount, parse_date  # reuse helpers

salary_bp = Blueprint("salary", __name__)


# ================== Salary Endpoints ==================

@salary_bp.route("/add", methods=["POST"])
@token_required
def add_salary(current_user):
    """Add a new salary record for the logged-in user."""
    try:
        data = request.get_json() or {}
        amount = clean_amount(data.get("amount"))
        salary_date = parse_date(data.get("salary_date"))

        if amount is None:
            return jsonify({"error": "Valid salary amount is required"}), 400
        if not salary_date:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        new_salary = Salary(
            user_id=current_user.id,
            amount=amount,
            salary_date=salary_date,
        )
        db.session.add(new_salary)
        db.session.commit()

        return jsonify({"message": "Salary added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /salary/add: {e}")
        return jsonify({"error": "Server error while adding salary"}), 500


@salary_bp.route("/history", methods=["GET"])
@token_required
def get_salary_history(current_user):
    """Fetch salary history for the logged-in user (latest first)."""
    try:
        salaries = (
            Salary.query.filter_by(user_id=current_user.id)
            .order_by(Salary.salary_date.desc())
            .all()
        )

        salary_list = [
            {
                "id": s.id,
                "amount": float(s.amount),
                "salary_date": s.salary_date.strftime("%Y-%m-%d") if s.salary_date else None,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
            }
            for s in salaries
        ]

        return jsonify({"data": salary_list}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /salary/history: {e}")
        return jsonify({"error": "Server error while fetching salary history"}), 500


@salary_bp.route("/update/<int:id>", methods=["PUT"])
@token_required
def update_salary(current_user, id):
    """Update a salary record (only if it belongs to the user)."""
    try:
        data = request.get_json() or {}
        salary = Salary.query.filter_by(id=id, user_id=current_user.id).first()
        if not salary:
            return jsonify({"error": "Salary record not found"}), 404

        if "amount" in data:
            new_amount = clean_amount(data["amount"])
            if new_amount is None:
                return jsonify({"error": "Amount must be a valid number"}), 400
            salary.amount = new_amount
        if "salary_date" in data:
            new_date = parse_date(data["salary_date"])
            if not new_date:
                return jsonify({"error": "Invalid date format"}), 400
            salary.salary_date = new_date

        db.session.commit()
        return jsonify({"message": "Salary updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /salary/update: {e}")
        return jsonify({"error": "Server error while updating salary"}), 500


@salary_bp.route("/delete/<int:id>", methods=["DELETE"])
@token_required
def delete_salary(current_user, id):
    """Delete a salary record (only if it belongs to the user)."""
    try:
        salary = Salary.query.filter_by(id=id, user_id=current_user.id).first()
        if not salary:
            return jsonify({"error": "Salary record not found"}), 404

        db.session.delete(salary)
        db.session.commit()
        return jsonify({"message": "Salary deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /salary/delete: {e}")
        return jsonify({"error": "Server error while deleting salary"}), 500