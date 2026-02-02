"""
=============================================================================
BESIKTNINGSAPP BACKEND - PROPERTIES ENDPOINTS
=============================================================================
Property CRUD endpoints: /properties
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy import or_

from app.extensions import db
from app.models import Property
from app.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyList,
    PaginationParams,
    PaginationMeta,
    ErrorResponse,
)

bp = Blueprint("properties", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_properties():
    """
    List all properties with pagination.
    
    Query params:
        - limit: int (1-100, default 50)
        - offset: int (default 0)
        - search: str (search in designation, address, city)
    
    Response: 200 OK with PropertyList
    """
    try:
        # Parse pagination params
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        search = request.args.get("search", "").strip()
        
        # Build query
        query = Property.query
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Property.designation.ilike(search_pattern),
                    Property.address.ilike(search_pattern),
                    Property.city.ilike(search_pattern),
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        properties = query.order_by(Property.created_at.desc()).limit(limit).offset(offset).all()
        
        # Build response
        return jsonify({
            "data": [PropertyResponse.from_orm(p).dict() for p in properties],
            "meta": PaginationMeta(
                total=total,
                limit=limit,
                offset=offset,
                has_more=(offset + limit) < total
            ).dict()
        }), 200
        
    except Exception as e:
        current_app.logger.exception(f"List properties error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:property_id>", methods=["GET"])
@jwt_required()
def get_property(property_id: int):
    """
    Get property by ID.
    
    Response: 200 OK with PropertyResponse
              404 Not Found
    """
    try:
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify(ErrorResponse.not_found("Property not found").dict()), 404
        
        return jsonify({
            "data": PropertyResponse.from_orm(property).dict()
        }), 200
        
    except Exception as e:
        current_app.logger.exception(f"Get property error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("", methods=["POST"])
@jwt_required()
def create_property():
    """
    Create new property.
    
    Request: PropertyCreate
    Response: 201 Created with PropertyResponse
    """
    try:
        # Validate request
        data = PropertyCreate(**request.get_json())
        
        # Create property
        property = Property(
            client_id=data.client_id,
            property_type=data.property_type,
            designation=data.designation,
            owner=data.owner,
            address=data.address,
            postal_code=data.postal_code,
            city=data.city,
            num_apartments=data.num_apartments,
            num_premises=data.num_premises,
            notes=data.notes,
        )
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify({
            "data": PropertyResponse.from_orm(property).dict()
        }), 201
        
    except ValidationError as e:
        errors = [{"field": str(err["loc"][0]), "issue": err["msg"]} for err in e.errors()]
        return jsonify(ErrorResponse.validation_error(field_errors=errors).dict()), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Create property error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:property_id>", methods=["PATCH"])
@jwt_required()
def update_property(property_id: int):
    """
    Update property.
    
    Request: PropertyUpdate (with base_revision)
    Response: 200 OK with PropertyResponse
              404 Not Found
              409 Conflict (revision mismatch)
    """
    try:
        # Validate request
        data = PropertyUpdate(**request.get_json())
        
        # Find property
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify(ErrorResponse.not_found("Property not found").dict()), 404
        
        # Check revision (optimistic locking)
        if property.revision != data.base_revision:
            return jsonify(ErrorResponse.conflict(
                message="Revision mismatch",
                details={
                    "entity_type": "property",
                    "server_id": property_id,
                    "current_revision": property.revision,
                    "provided_revision": data.base_revision
                }
            ).dict()), 409
        
        # Update fields
        if data.property_type is not None:
            property.property_type = data.property_type
        if data.designation is not None:
            property.designation = data.designation
        if data.owner is not None:
            property.owner = data.owner
        if data.address is not None:
            property.address = data.address
        if data.postal_code is not None:
            property.postal_code = data.postal_code
        if data.city is not None:
            property.city = data.city
        if data.num_apartments is not None:
            property.num_apartments = data.num_apartments
        if data.num_premises is not None:
            property.num_premises = data.num_premises
        if data.notes is not None:
            property.notes = data.notes
        
        db.session.commit()
        
        return jsonify({
            "data": PropertyResponse.from_orm(property).dict()
        }), 200
        
    except ValidationError as e:
        errors = [{"field": str(err["loc"][0]), "issue": err["msg"]} for err in e.errors()]
        return jsonify(ErrorResponse.validation_error(field_errors=errors).dict()), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Update property error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/<int:property_id>", methods=["DELETE"])
@jwt_required()
def delete_property(property_id: int):
    """
    Delete property.
    
    Response: 204 No Content
              404 Not Found
    """
    try:
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify(ErrorResponse.not_found("Property not found").dict()), 404
        
        db.session.delete(property)
        db.session.commit()
        
        return "", 204
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Delete property error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500
