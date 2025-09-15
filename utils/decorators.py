from functools import wraps
from flask import request, jsonify
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from models.user import User
from config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token missing!"}), 403

        # ✅ Handle Bearer prefix
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                return jsonify({"message": "User not found!"}), 404
        except ExpiredSignatureError:
            return jsonify({"message": "Token expired!"}), 401
        except InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 403
        except Exception as e:
            return jsonify({"message": f"Auth error: {str(e)}"}), 500

        return f(current_user, *args, **kwargs)
    return decorated
