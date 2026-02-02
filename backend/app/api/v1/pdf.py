"""PDF endpoints: /pdf/generate, /pdf/versions"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import PDFVersion, Inspection
from app.schemas import PDFVersionResponse, ErrorResponse

bp = Blueprint("pdf", __name__)

@bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_pdf():
    """Generate PDF for inspection."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        inspection_id = data.get("inspection_id")
        status = data.get("status", "draft")
        
        if not inspection_id:
            return jsonify(ErrorResponse.validation_error("inspection_id required").dict()), 400
        
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify(ErrorResponse.not_found("Inspection not found").dict()), 404
        
        # TODO: Implement PDF generation logic
        # - Get next version number
        # - Generate PDF using pdf_service
        # - Store in storage_service
        # - Create PDFVersion record
        
        return jsonify({
            "data": {
                "id": 1,
                "version_number": 1,
                "status": status,
                "url": "https://placeholder.com/pdf.pdf",
                "filename": f"besiktning_{inspection_id}_v1.pdf",
                "size_bytes": 524288,
                "checksum": "sha256:placeholder",
                "created_at": "2026-01-29T12:00:00Z"
            }
        }), 201
    except Exception as e:
        current_app.logger.exception(f"Generate PDF error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/versions/<int:inspection_id>", methods=["GET"])
@jwt_required()
def list_pdf_versions(inspection_id: int):
    """List all PDF versions for inspection."""
    try:
        versions = PDFVersion.query.filter_by(inspection_id=inspection_id).order_by(PDFVersion.version_number.desc()).all()
        return jsonify({
            "data": [PDFVersionResponse.from_orm(v).dict() for v in versions],
            "meta": {"total": len(versions)}
        }), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/versions/<int:version_id>", methods=["GET"])
@jwt_required()
def get_pdf_version(version_id: int):
    """Get specific PDF version."""
    try:
        version = PDFVersion.query.get(version_id)
        if not version:
            return jsonify(ErrorResponse.not_found().dict()), 404
        return jsonify({"data": PDFVersionResponse.from_orm(version).dict()}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500
