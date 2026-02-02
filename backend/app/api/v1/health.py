"""Health check endpoints: /health, /ready"""
from flask import Blueprint, jsonify, current_app
from app.extensions import db

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health():
    """Liveness probe."""
    return jsonify({
        "status": "healthy",
        "service": "besiktningsapp-backend",
        "version": "1.0.0"
    }), 200

@bp.route("/ready", methods=["GET"])
def ready():
    """Readiness probe."""
    checks = {"database": False}
    try:
        db.session.execute(db.text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        current_app.logger.error(f"Database check failed: {e}")
    
    all_healthy = all(checks.values())
    return jsonify({
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }), 200 if all_healthy else 503
