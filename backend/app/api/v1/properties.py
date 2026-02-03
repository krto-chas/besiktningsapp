"""
=============================================================================
BESIKTNINGSAPP BACKEND - PROPERTIES API
=============================================================================
REST API endpoints for Property operations.

Endpoints:
- POST   /properties           - Create property
- GET    /properties           - List properties
- GET    /properties/search    - Search properties
- GET    /properties/:id       - Get property
- PUT    /properties/:id       - Update property
- DELETE /properties/:id       - Delete property
- GET    /properties/:id/inspections - Get property inspections
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.property_service import PropertyService
from app.services.inspection_service import InspectionService
from app.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyList,
    PaginationParams,
    StandardResponse,
    ErrorResponse,
)
from app.utils.errors import NotFoundError, ConflictError, ValidationError
from app.utils.decorators import rate_limit

properties_bp = Blueprint('properties', __name__, url_prefix='/properties')


# =============================================================================
# CREATE
# =============================================================================

@properties_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit("10/minute")
def create_property():
    """
    Create new property.

    Request Body (PropertyCreate):
        {
            "property_type": "flerbostadshus",
            "designation": "Kungsholmen 1:1",
            "address": "Hantverkargatan 12",
            "postal_code": "112 21",
            "city": "Stockholm",
            "owner": "Fastighets AB",
            "num_apartments": 48,
            "construction_year": 1985,
            "client_id": "optional-uuid"
        }

    Returns:
        201: Created property
        400: Validation error
        409: Duplicate client_id
        429: Rate limit exceeded
    """
    try:
        # Validate request body
        data = PropertyCreate(**request.get_json())
        
        # Get current user
        user_id = get_jwt_identity()
        
        # Create property
        property_obj = PropertyService.create_property(
            data=data.model_dump(),
            user_id=user_id
        )
        
        # Return response
        response = PropertyResponse.model_validate(property_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 201
        
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# READ
# =============================================================================

@properties_bp.route('', methods=['GET'])
@jwt_required()
def list_properties():
    """
    List properties with pagination.

    Query Parameters:
        - limit: int (default 50, max 100)
        - offset: int (default 0)
        - user_id: int (optional, filter by creator)

    Returns:
        200: List of properties with pagination metadata
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        user_id_filter = request.args.get('user_id', type=int)
        
        # Get properties
        properties, total = PropertyService.list_properties(
            limit=limit,
            offset=offset,
            user_id=user_id_filter
        )
        
        # Build response
        response = PropertyList(
            data=[PropertyResponse.model_validate(p) for p in properties],
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@properties_bp.route('/search', methods=['GET'])
@jwt_required()
def search_properties():
    """
    Search properties by designation, address, city, or owner.

    Query Parameters:
        - q: str (search term, required)
        - limit: int (default 50, max 100)
        - offset: int (default 0)

    Returns:
        200: Search results with pagination
        400: Missing search term
    """
    try:
        # Get search term
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify(ErrorResponse.validation_error(
                "Search term 'q' is required"
            ).model_dump()), 400
        
        # Parse pagination
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Search
        properties, total = PropertyService.search_properties(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
        
        # Build response
        response = PropertyList(
            data=[PropertyResponse.model_validate(p) for p in properties],
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'search_term': search_term,
                'has_more': (offset + limit) < total
            }
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@properties_bp.route('/<int:property_id>', methods=['GET'])
@jwt_required()
def get_property(property_id):
    """
    Get property by ID.

    Path Parameters:
        - property_id: int

    Returns:
        200: Property data
        404: Property not found
    """
    try:
        property_obj = PropertyService.get_property(property_id)
        response = PropertyResponse.model_validate(property_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@properties_bp.route('/<int:property_id>/inspections', methods=['GET'])
@jwt_required()
def get_property_inspections(property_id):
    """
    Get all inspections for a property.

    Path Parameters:
        - property_id: int

    Query Parameters:
        - limit: int (default 50, max 100)
        - offset: int (default 0)

    Returns:
        200: List of inspections
        404: Property not found
    """
    try:
        # Verify property exists
        PropertyService.get_property(property_id)
        
        # Parse pagination
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Get inspections
        from app.schemas import InspectionResponse, InspectionList
        inspections, total = InspectionService.get_property_inspections(
            property_id=property_id,
            limit=limit,
            offset=offset
        )
        
        # Build response
        response = InspectionList(
            data=[InspectionResponse.model_validate(i) for i in inspections],
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        )
        
        return jsonify(response.model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# UPDATE
# =============================================================================

@properties_bp.route('/<int:property_id>', methods=['PUT'])
@jwt_required()
@rate_limit("20/minute")
def update_property(property_id):
    """
    Update property with optimistic locking.

    Path Parameters:
        - property_id: int

    Request Body (PropertyUpdate):
        {
            "base_revision": 1,
            "property_type": "flerbostadshus",
            "address": "New address",
            ...
        }

    Returns:
        200: Updated property
        400: Validation error
        404: Property not found
        409: Revision conflict
        429: Rate limit exceeded
    """
    try:
        # Validate request body
        data = PropertyUpdate(**request.get_json())
        
        # Update property
        property_obj = PropertyService.update_property(
            property_id=property_id,
            data=data.model_dump(exclude={'base_revision'}, exclude_none=True),
            base_revision=data.base_revision
        )
        
        # Return response
        response = PropertyResponse.model_validate(property_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# DELETE
# =============================================================================

@properties_bp.route('/<int:property_id>', methods=['DELETE'])
@jwt_required()
@rate_limit("10/minute")
def delete_property(property_id):
    """
    Soft delete property.

    Path Parameters:
        - property_id: int

    Returns:
        200: Property deleted
        404: Property not found
        400: Cannot delete (has inspections)
        429: Rate limit exceeded
    """
    try:
        # Check if can delete
        can_delete, reason = PropertyService.can_delete(property_id)
        if not can_delete:
            return jsonify(ErrorResponse.validation_error(reason).model_dump()), 400
        
        # Delete property
        deleted = PropertyService.delete_property(property_id)
        
        if deleted:
            return jsonify(StandardResponse(
                data={'message': 'Property deleted successfully'}
            ).model_dump()), 200
        else:
            return jsonify(StandardResponse(
                data={'message': 'Property already deleted'}
            ).model_dump()), 200
            
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# STATISTICS
# =============================================================================

@properties_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    Get property statistics.

    Query Parameters:
        - user_id: int (optional, filter by user)

    Returns:
        200: Statistics data
    """
    try:
        user_id = request.args.get('user_id', type=int)
        stats = PropertyService.get_statistics(user_id=user_id)
        return jsonify(StandardResponse(data=stats).model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@properties_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(ErrorResponse.not_found().model_dump()), 404


@properties_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify(ErrorResponse.internal_error().model_dump()), 500