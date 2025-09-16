from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__)


# ✅ Register user
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        # Create new user
        hashed_pw = generate_password_hash(password)
        new_user = User(email=email, password=hashed_pw, salary=0.0)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully", "email": email}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Login user
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify({
            "message": "Login successful",
            "email": user.email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get user profile (salary + expenses)
@auth_bp.route("/user/<string:email>", methods=["GET"])
def get_user_profile(email):
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "email": user.email,
            "salary": user.salary,
            "expenses": [
                {
                    "id": exp.id,
                    "amount": exp.amount,
                    "category": exp.category,
                    "date": exp.date.isoformat() if exp.date else None,
                    "time": exp.time.isoformat() if exp.time else None,
                    "description": exp.description,
                }
                for exp in user.expenses
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500