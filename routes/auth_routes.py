from flask import Blueprint, request, jsonify
from models.user import User
from app import db
import jwt
from datetime import datetime, timedelta
from config import Config

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 400

    new_user = User(username=data["username"], email=data["email"])
    new_user.set_password(data["password"])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
        Config.SECRET_KEY,
        algorithm="HS256"
    )
    return jsonify({"token": token})