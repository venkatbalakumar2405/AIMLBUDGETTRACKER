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

def generate_token(user_id: int, expires_in_hours: int = None) -> str:
    """Generate a JWT token for a user."""
    exp_hours = expires_in_hours or int(os.getenv("JWT_EXP_HOURS", 12))

    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=exp_hours),
    }

    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is missing in app config")

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")


def token_required(f):
    """Decorator: protect routes with JWT authentication."""
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
        except Exception as e:
            current_app.logger.exception(f"❌ Token validation failed: {e}")
            return jsonify({"error": "Authentication failed"}), 401

        return f(user, *args, **kwargs)
    return decorated


def get_request_data(required_fields):
    """Helper: safely extract and validate request JSON data."""
    data = request.get_json(silent=True) or {}
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return None, jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    return data, None, None


# ================== AUTH ROUTES ==================

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user with email, password, salary, and budget limit."""
    data, error_response, status = get_request_data(["email", "password"])
    if error_response:
        return error_response, status

    try:
        email, password = data["email"].lower().strip(), data["password"]

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        hashed_password = generate_password_hash(password)

        new_user = User(
            email=email,
            password=hashed_password,
            salary=float(data.get("salary", 0)),
            budget_limit=float(data.get("budget_limit", 0)),
        )

        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"✅ User registered: {email}")
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"❌ Error in /auth/register: {e}")
        return jsonify({"error": "Server error while registering user"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with email and password to receive a JWT access & refresh token."""
    data, error_response, status = get_request_data(["email", "password"])
    if error_response:
        return error_response, status

    try:
        email, password = data["email"].lower().strip(), data["password"]

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        access_token = generate_token(user.id, expires_in_hours=1)   # short-lived
        refresh_token = generate_token(user.id, expires_in_hours=24) # long-lived

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "email": user.email,
            "salary": float(user.salary or 0),
            "budget_limit": float(user.budget_limit or 0),
        }), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /auth/login: {e}")
        return jsonify({"error": "Server error while logging in"}), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using a valid refresh token."""
    data, error_response, status = get_request_data(["refresh_token"])
    if error_response:
        return error_response, status

    try:
        token = data["refresh_token"]

        decoded = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
        user_id = decoded.get("user_id")
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "Invalid refresh token"}), 401

        # issue new access token
        new_access_token = generate_token(user.id, expires_in_hours=1)

        return jsonify({
            "access_token": new_access_token
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired, please login again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid refresh token"}), 401
    except Exception as e:
        current_app.logger.exception(f"❌ Error in /auth/refresh: {e}")
        return jsonify({"error": "Server error while refreshing token"}), 500


# ================== USER PROFILE ==================

@auth_bp.route("/user/<email>", methods=["GET"])
@token_required
def get_user(current_user, email):
    """Fetch user profile, salary, budget, and expenses (authorized only)."""
    try:
        if current_user.email != email.lower().strip():
            return jsonify({"error": "Unauthorized access"}), 403

        return jsonify({
            "email": current_user.email,
            "salary": float(current_user.salary or 0),
            "budget_limit": float(current_user.budget_limit or 0),
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": float(e.amount),
                    "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                    "category": e.category or "Miscellaneous",
                }
                for e in current_user.expenses
            ],
        }), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error in /auth/user/<email>: {e}")
        return jsonify({"error": "Server error while fetching user"}), 500
