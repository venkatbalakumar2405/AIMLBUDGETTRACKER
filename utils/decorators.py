from functools import wraps
from flask import request, jsonify, current_app
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from models import User


def token_required(f):
    """
    Decorator to protect routes with JWT authentication.
    Attaches the current_user to the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # ✅ Handle Bearer prefix
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            decoded = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            current_user = User.query.get(decoded.get("user_id"))
            if not current_user:
                return jsonify({"error": "User not found"}), 404

        except ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 403
        except Exception as e:
            current_app.logger.exception("❌ Token validation failed: %s", e)
            return jsonify({"error": f"Auth error: {str(e)}"}), 500

        return f(current_user, *args, **kwargs)
    return decorated