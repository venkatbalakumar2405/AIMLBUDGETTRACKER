from flask import Blueprint, request, jsonify
from utils.extensions import db
from models.user import User
from models.expense import Expense
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

# ✅ Health check / test route
@auth_bp.route("/", methods=["GET"])
def auth_home():
    return jsonify({"message": "Auth API is working!"})


# ✅ Register new user
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    user = User(email=email, password=hashed_password, salary=0)  # default salary = 0
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


# ✅ Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "email": email})


# ✅ Get user profile (salary + expenses)
@auth_bp.route("/user/<email>", methods=["GET"])
def get_user(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify({
        "email": user.email,
        "salary": user.salary,
        "expenses": [
            {"id": e.id, "amount": e.amount, "description": e.description}
            for e in expenses
        ]
    })