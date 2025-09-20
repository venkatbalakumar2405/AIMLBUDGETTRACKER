from flask import Blueprint, jsonify
from datetime import datetime

home_bp = Blueprint("home", __name__)

API_NAME = "Budget Tracker API"
API_VERSION = "1.0.0"


# ================== Root Endpoint ==================
@home_bp.route("/", methods=["GET"])
def root():
    """Root API endpoint - confirms service is running."""
    return jsonify({
        "message": f"{API_NAME} is running 🚀",
        "status": "ok",
        "version": API_VERSION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }), 200


# ================== Health Check ==================
@home_bp.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "version": API_VERSION
    }), 200
