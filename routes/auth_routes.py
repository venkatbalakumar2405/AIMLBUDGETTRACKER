from flask import Blueprint, jsonify
from models.user import User

auth_bp = Blueprint("auth", __name__)

# ... your register and login routes ...

# ✅ Get User Profile by Email
@auth_bp.route("/user/<email>", methods=["GET"])
def get_user(email):
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "email": user.email,
            "salary": float(user.salary or 0),
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": float(e.amount),
                    "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                }
                for e in user.expenses
            ],
        }), 200
    except Exception as e:
        print("❌ Error in /auth/user/<email>:", str(e))
        return jsonify({"error": "Server error while fetching user"}), 500