from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from utils.extensions import db
import jwt
import datetime

auth_bp = Blueprint("auth", __name__)

# ✅ Register Route
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        salary = data.get("salary", 0)
        budget_limit = data.get("budget_limit", 0)

        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create new user
        new_user = User(
            email=email,
            password_hash=hashed_password,
            salary=salary,
            budget_limit=budget_limit,
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        current_app.logger.exception("❌ Register error")
        return jsonify({"error": str(e)}), 500


# ✅ Login Route
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT
        token = jwt.encode(
            {
                "id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "salary": user.salary,
                "budget_limit": user.budget_limit
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("❌ Login error")
        return jsonify({"error": str(e)}), 500