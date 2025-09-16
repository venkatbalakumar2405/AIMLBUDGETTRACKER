from flask import Blueprint, request, jsonify
from models.user import User
from utils.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from flask import current_app

auth_bp = Blueprint("auth", __name__)

# ================== REGISTER ==================
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, salary=0)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        print("❌ Error in /auth/register:", str(e))
        return jsonify({"error": "Server error while registering user"}), 500


# ================== LOGIN ==================
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

        # 🔹 Generate JWT token
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

        return jsonify({"token": token, "email": user.email}), 200
    except Exception as e:
        print("❌ Error in /auth/login:", str(e))
        return jsonify({"error": "Server error while logging in"}), 500


# ================== USER PROFILE ==================
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
                    "category": e.category,
                }
                for e in user.expenses
            ],
        }), 200
    except Exception as e:
        print("❌ Error in /auth/user/<email>:", str(e))
        return jsonify({"error": "Server error while fetching user"}), 500