from flask import Blueprint, jsonify

home_bp = Blueprint("home", __name__)

# ✅ Root endpoint - Health Check
@home_bp.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Budget Tracker API! 🚀"})