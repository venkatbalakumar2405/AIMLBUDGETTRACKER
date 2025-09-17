from flask import Blueprint, jsonify
from datetime import datetime

home_bp = Blueprint("home", __name__)


# ================== Root Endpoint ==================

@home_bp.route("/", methods=["GET"])
def home():
    """Root API endpoint - basic info and health check."""
    return jsonify({
        "message": "Welcome to the Budget Tracker API 🚀",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }), 200


# ================== Health Check ==================

@home_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }), 200