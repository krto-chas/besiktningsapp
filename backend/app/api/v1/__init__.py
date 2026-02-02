"""
=============================================================================
BESIKTNINGSAPP BACKEND - API V1
=============================================================================
API version 1 blueprint registration.

All v1 endpoints are registered here and exposed via api_v1_bp.
"""

from flask import Blueprint

# Create main v1 blueprint
api_v1_bp = Blueprint("api_v1", __name__)

# Import and register sub-blueprints
from app.api.v1 import (
    auth,
    properties,
    inspections,
    apartments,
    defects,
    images,
    measurements,
    sync,
    pdf,
    export,
    health,
)

# Register routes from modules
# Auth routes
api_v1_bp.register_blueprint(auth.bp, url_prefix="/auth")

# Resource routes
api_v1_bp.register_blueprint(properties.bp, url_prefix="/properties")
api_v1_bp.register_blueprint(inspections.bp, url_prefix="/inspections")
api_v1_bp.register_blueprint(apartments.bp, url_prefix="/apartments")
api_v1_bp.register_blueprint(defects.bp, url_prefix="/defects")
api_v1_bp.register_blueprint(measurements.bp, url_prefix="/measurements")

# Upload routes
api_v1_bp.register_blueprint(images.bp, url_prefix="/uploads")

# Sync routes
api_v1_bp.register_blueprint(sync.bp, url_prefix="/sync")

# PDF routes
api_v1_bp.register_blueprint(pdf.bp, url_prefix="/pdf")

# Export routes
api_v1_bp.register_blueprint(export.bp, url_prefix="/export")

# Health routes (no prefix - /health, /ready)
api_v1_bp.register_blueprint(health.bp)

__all__ = ["api_v1_bp"]
