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

# Core blueprints (always required)
from app.api.v1.auth import bp as auth_bp
from app.api.v1.properties import properties_bp
from app.api.v1.inspections import inspections_bp
from app.api.v1.apartments import apartments_bp
from app.api.v1.images import images_bp

# Feature blueprints
from app.api.v1.defects import bp as defects_bp
from app.api.v1.measurements import bp as measurements_bp
from app.api.v1.sync import bp as sync_bp
from app.api.v1.pdf import bp as pdf_bp
from app.api.v1.export import bp as export_bp
from app.api.v1.health import bp as health_bp

# Register all blueprints with URL prefixes
api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_v1_bp.register_blueprint(properties_bp, url_prefix="/properties")
api_v1_bp.register_blueprint(inspections_bp, url_prefix="/inspections")
api_v1_bp.register_blueprint(apartments_bp, url_prefix="/apartments")
api_v1_bp.register_blueprint(images_bp, url_prefix="/images")
api_v1_bp.register_blueprint(defects_bp, url_prefix="/defects")
api_v1_bp.register_blueprint(measurements_bp, url_prefix="/measurements")
api_v1_bp.register_blueprint(sync_bp, url_prefix="/sync")
api_v1_bp.register_blueprint(pdf_bp, url_prefix="/pdf")
api_v1_bp.register_blueprint(export_bp, url_prefix="/export")
api_v1_bp.register_blueprint(health_bp)

__all__ = ["api_v1_bp"]
