from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.user import User


def token_required(f):
    """
    JWT-based route protection.
    - Expects header: Authorization: Bearer <token>
    - Decodes token, validates user
    - Injects current_user into route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            user = User.query.get(decoded.get("user_id"))
            if not user:
                return jsonify({"error": "Invalid token user"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            current_app.logger.exception("❌ Token validation failed: %s", e)
            return jsonify({"error": "Authentication failed"}), 401

        # Pass current_user into the route
        return f(user, *args, **kwargs)

    return decorated