"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTIONS ENDPOINTS
=============================================================================
Inspection CRUD endpoints: /inspections
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.extensions import db
from app.models import Inspection, Property
from app.schemas import InspectionCreate, InspectionUpdate, InspectionResponse, ErrorResponse

bp = Blueprint("inspections", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_inspections():
    """List inspections with optional property_id filter."""
    try:
        property_id = request.args.get("property_id", type=int)
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        
        query = Inspection.query
        if property_id:
            query = query.filter_by(property_id=property_id)
        
        total = query.count()
        inspections = query.order_by(Inspection.date.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            "data": [InspectionResponse.from_orm(i).dict() for i in inspections],
            "meta": {"total": total, "limit": limit, "offset": offset, "has_more": (offset + limit) < total}
        }), 200
    except Exception as e:
        current_app.logger.exception(f"List inspections error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:inspection_id>", methods=["GET"])
@jwt_required()
def get_inspection(inspection_id: int):
    """Get inspection by ID."""
    try:
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify(ErrorResponse.not_found().dict()), 404
        return jsonify({"data": InspectionResponse.from_orm(inspection).dict()}), 200
    except Exception as e:
        current_app.logger.exception(f"Get inspection error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("", methods=["POST"])
@jwt_required()
def create_inspection():
    """Create new inspection."""
    try:
        user_id = get_jwt_identity()
        data = InspectionCreate(**request.get_json())
        
        # Resolve property_id
        property_id = data.property_id
        if not property_id and data.property_client_id:
            prop = Property.query.filter_by(client_id=data.property_client_id).first()
            if prop:
                property_id = prop.id
        
        if not property_id:
            return jsonify(ErrorResponse.validation_error("property_id or property_client_id required").dict()), 400
        
        inspection = Inspection(
            client_id=data.client_id,
            property_id=property_id,
            inspector_id=user_id,
            date=data.date,
            active_time_seconds=data.active_time_seconds,
            status=data.status,
            notes=data.notes,
        )
        
        db.session.add(inspection)
        db.session.commit()
        
        return jsonify({"data": InspectionResponse.from_orm(inspection).dict()}), 201
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Create inspection error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:inspection_id>", methods=["PATCH"])
@jwt_required()
def update_inspection(inspection_id: int):
    """Update inspection."""
    try:
        data = InspectionUpdate(**request.get_json())
        inspection = Inspection.query.get(inspection_id)
        
        if not inspection:
            return jsonify(ErrorResponse.not_found().dict()), 404
        
        if inspection.revision != data.base_revision:
            return jsonify(ErrorResponse.conflict().dict()), 409
        
        if data.date: inspection.date = data.date
        if data.active_time_seconds is not None: inspection.active_time_seconds = data.active_time_seconds
        if data.status: inspection.status = data.status
        if data.notes is not None: inspection.notes = data.notes
        
        db.session.commit()
        return jsonify({"data": InspectionResponse.from_orm(inspection).dict()}), 200
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Update inspection error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:inspection_id>", methods=["DELETE"])
@jwt_required()
def delete_inspection(inspection_id: int):
    """Delete inspection."""
    try:
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify(ErrorResponse.not_found().dict()), 404
        db.session.delete(inspection)
        db.session.commit()
        return "", 204
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Delete inspection error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500
