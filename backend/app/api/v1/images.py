"""Image upload endpoints: /uploads/images, /uploads/presign"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.schemas import ErrorResponse

bp = Blueprint("images", __name__)

@bp.route("/images", methods=["POST"])
@jwt_required()
def upload_image():
    """Direct image upload (multipart/form-data)."""
    try:
        if 'file' not in request.files:
            return jsonify(ErrorResponse.validation_error("No file provided").dict()), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(ErrorResponse.validation_error("Empty filename").dict()), 400
        
        # TODO: Implement actual storage via storage_service
        # For now, return placeholder
        return jsonify({
            "data": {
                "id": 1,
                "url": "https://placeholder.com/image.jpg",
                "storage_key": "images/placeholder.jpg",
                "filename": secure_filename(file.filename),
                "checksum": "sha256:placeholder",
                "created_at": "2026-01-29T12:00:00Z"
            }
        }), 201
    except Exception as e:
        current_app.logger.exception(f"Upload image error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/presign", methods=["POST"])
@jwt_required()
def presign_upload():
    """Get presigned upload URL (for S3/MinIO)."""
    try:
        # TODO: Implement presigned URL generation
        return jsonify({
            "data": {
                "upload_url": "https://placeholder.com/upload",
                "storage_key": "images/placeholder.jpg",
                "expires_at": "2026-01-29T13:00:00Z"
            }
        }), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/complete", methods=["POST"])
@jwt_required()
def complete_upload():
    """Complete presigned upload."""
    try:
        # TODO: Implement upload completion
        return jsonify({
            "data": {
                "id": 1,
                "url": "https://placeholder.com/image.jpg"
            }
        }), 201
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500
