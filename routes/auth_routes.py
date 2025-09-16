from flask import Blueprint, request, jsonify, current_app
from models.user import User
from utils.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps

auth_bp = Blueprint("auth", __name__)


# ================== HELPER FUNCTIONS ==================

def generate_token(user_id: int) -> str:
    """Generate a JWT token for the given user ID."""
    try:
        exp_hours = int(os.getenv("JWT_EXP_HOURS", 12))  # configurable expiry
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=exp_hours),
        }
        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
        return token
    except Exception:
        current_app.logger.exception("❌ Failed to generate token")
        raise


def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[-1]  # Bearer <token>

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            user = User.query.get(data.get("user_id"))
            if not user:
                return jsonify({"error": "Invalid token user"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception:
            current_app.logger.exception("❌ Token validation failed")
            return jsonify({"error": "Authentication failed"}), 401

        return f(user, *args, **kwargs)
    return decorated


def get_request_data(required_fields):
    """Helper to safely extract required fields from request JSON."""
    data = request.get_json(silent=True) or {}
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return None, jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    return data, None, None


# ================== AUTH ROUTES ==================

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data, error_response, status = get_request_data(["email", "password"])
        if error_response:
            return error_response, status

        email, password = data["email"], data["password"]

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, salary=0)

        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"✅ User registered: {email}")
        return jsonify({"message": "User registered successfully"}), 201

    except Exception:
        current_app.logger.exception("❌ Error in /auth/register")
        return jsonify({"error": "Server error while registering user"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data, error_response, status = get_request_data(["email", "password"])
        if error_response:
            return error_response, status

        email, password = data["email"], data["password"]

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        token = generate_token(user.id)

        return jsonify({
            "token": token,
            "email": user.email,
        }), 200

    except Exception:
        current_app.logger.exception("❌ Error in /auth/login")
        return jsonify({"error": "Server error while logging in"}), 500


# ================== USER PROFILE ==================

@auth_bp.route("/user/<email>", methods=["GET"])
@token_required
def get_user(current_user, email):
    try:
        if current_user.email != email:
            return jsonify({"error": "Unauthorized access"}), 403

        return jsonify({
            "email": current_user.email,
            "salary": float(current_user.salary or 0),
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": float(e.amount),
                    "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                    "category": e.category,
                }
                for e in current_user.expenses
            ],
        }), 200

    except Exception:
        current_app.logger.exception("❌ Error in /auth/user/<email>")
        return jsonify({"error": "Server error while fetching user"}), 500