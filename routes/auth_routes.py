from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os

from models.user import User
from models.expense import Expense
from utils.extensions import db
from utils.decorators import token_required
from routes.budget_routes import build_summary


# ================== Blueprint Setup ================== #
auth_bp = Blueprint("auth", __name__)


# ================== HELPER FUNCTIONS ================== #
def _get_jwt_secret():
    """Safely fetch the JWT secret key from config or env."""
    secret = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is missing in configuration")
    return secret


def generate_token(user_id: int, expires_in_hours: int | None = None) -> str:
    """Generate a JWT token for a user with expiration."""
    exp_hours = expires_in_hours or int(os.getenv("JWT_EXP_HOURS", 12))

    payload = {
        "user_id": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=exp_hours),
    }

    token = jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")


def get_request_data(required_fields: list[str]):
    """Helper: safely extract and validate request JSON data."""
    data = request.get_json(silent=True) or {}
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return None, jsonify({
            "status": "error",
            "message": f"Missing fields: {', '.join(missing)}"
        }), 400
    return data, None, None


# ================== AUTH ROUTES ================== #
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user with email, password, salary, and budget limit."""
    data, error_response, status = get_request_data(["email", "password"])
    if error_response:
        return error_response, status

    try:
        email, password = data["email"].lower().strip(), data["password"]
        current_app.logger.info("📩 Register attempt for %s", email)

        if User.query.filter_by(email=email).first():
            return jsonify({"status": "error", "message": "User already exists"}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password=hashed_password,
            salary=float(data.get("salary", 0.0)),
            budget_limit=float(data.get("budget_limit", 0.0)),
        )

        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info("✅ User registered successfully: %s", email)
        return jsonify({
            "status": "success",
            "message": "User registered successfully",
            "user_id": new_user.id,
            "email": new_user.email
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Registration failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with email and password to receive JWT access & refresh tokens."""
    data, error_response, status = get_request_data(["email", "password"])
    if error_response:
        return error_response, status

    try:
        email, password = data["email"].lower().strip(), data["password"]
        current_app.logger.info("🔑 Login attempt for %s", email)

        user = User.query.filter_by(email=email).first()
        if not user:
            current_app.logger.warning("❌ No user found for email: %s", email)
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401

        if not check_password_hash(user.password, password):
            current_app.logger.warning("❌ Invalid password for %s", email)
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401

        access_token = generate_token(user.id, expires_in_hours=1)    # short-lived
        refresh_token = generate_token(user.id, expires_in_hours=24) # long-lived

        expenses = Expense.query.filter_by(user_id=user.id).all()
        summary = build_summary(user, expenses)

        current_app.logger.info("✅ Login successful for %s", email)
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "profile": {
                "email": user.email,
                "salary": float(user.salary or 0),
                "budget_limit": float(user.budget_limit or 0),
            },
            "summary": summary
        }), 200

    except Exception as e:
        current_app.logger.exception("❌ Login failed for %s", data.get("email"))
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using a valid refresh token."""
    data, error_response, status = get_request_data(["refresh_token"])
    if error_response:
        return error_response, status

    try:
        decoded = jwt.decode(
            data["refresh_token"],
            _get_jwt_secret(),
            algorithms=["HS256"]
        )
        user = User.query.get(decoded.get("user_id"))
        if not user:
            return jsonify({"status": "error", "message": "Invalid refresh token"}), 401

        new_access_token = generate_token(user.id, expires_in_hours=1)
        current_app.logger.info("🔄 Access token refreshed for user %s", user.email)
        return jsonify({
            "status": "success",
            "access_token": new_access_token
        }), 200

    except jwt.ExpiredSignatureError:
        current_app.logger.warning("⚠️ Refresh token expired")
        return jsonify({"status": "error", "message": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        current_app.logger.warning("⚠️ Invalid refresh token")
        return jsonify({"status": "error", "message": "Invalid refresh token"}), 401
    except Exception as e:
        current_app.logger.exception("❌ Refresh token failed")
        return jsonify({"status": "error", "message": str(e)}), 500


# ================== USER PROFILE ================== #
@auth_bp.route("/user/<email>", methods=["GET"])
@token_required
def get_user_profile(current_user, email: str):
    """Fetch user profile, salary, budget, and expenses (authorized only)."""
    try:
        if current_user.email != email.lower().strip():
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        summary = build_summary(current_user, expenses)

        current_app.logger.info("👤 Profile fetched for %s", current_user.email)
        return jsonify({
            "status": "success",
            "email": current_user.email,
            "salary": float(current_user.salary or 0),
            "budget_limit": float(current_user.budget_limit or 0),
            "summary": summary,
            "expenses": [
                {
                    "id": exp.id,
                    "description": exp.description,
                    "amount": float(exp.amount),
                    "date": exp.date.strftime("%Y-%m-%d %H:%M:%S") if exp.date else None,
                    "category": exp.category or "Miscellaneous",
                }
                for exp in expenses
            ],
        }), 200

    except Exception as e:
        current_app.logger.exception("❌ Failed to fetch profile for %s", email)
        return jsonify({"status": "error", "message": str(e)}), 500