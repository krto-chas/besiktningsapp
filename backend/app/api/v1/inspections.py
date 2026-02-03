"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTIONS API
=============================================================================
REST API endpoints for Inspection operations.

Endpoints:
- POST   /inspections              - Create inspection
- GET    /inspections              - List inspections
- GET    /inspections/search       - Search inspections
- GET    /inspections/:id          - Get inspection
- PUT    /inspections/:id          - Update inspection
- DELETE /inspections/:id          - Delete inspection
- PATCH  /inspections/:id/status   - Change status
- PATCH  /inspections/:id/timer    - Update active time
- GET    /inspections/:id/summary  - Get inspection summary
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.inspection_service import InspectionService
from app.schemas import (
    InspectionCreate,
    InspectionUpdate,
    InspectionResponse,
    InspectionList,
    StandardResponse,
    ErrorResponse,
)
from app.utils.errors import NotFoundError, ConflictError, ValidationError
from app.utils.decorators import rate_limit

inspections_bp = Blueprint('inspections', __name__, url_prefix='/inspections')


# =============================================================================
# CREATE
# =============================================================================

@inspections_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit("10/minute")
def create_inspection():
    """
    Create new inspection.

    Request Body (InspectionCreate):
        {
            "property_id": 1,
            "date": "2026-02-03",
            "active_time_seconds": 0,
            "status": "draft",
            "notes": "OVK-besiktning",
            "client_id": "optional-uuid"
        }

    Returns:
        201: Created inspection
        400: Validation error
        404: Property not found
        409: Duplicate client_id
    """
    try:
        # Validate request body
        data = InspectionCreate(**request.get_json())
        
        # Get current user (inspector)
        user_id = get_jwt_identity()
        
        # Create inspection
        inspection_obj = InspectionService.create_inspection(
            data=data.model_dump(),
            user_id=user_id
        )
        
        # Return response
        response = InspectionResponse.model_validate(inspection_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 201
        
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# READ
# =============================================================================

@inspections_bp.route('', methods=['GET'])
@jwt_required()
def list_inspections():
    """
    List inspections with pagination and filters.

    Query Parameters:
        - limit: int (default 50, max 100)
        - offset: int (default 0)
        - status: str (optional, filter by status)
        - inspector_id: int (optional, filter by inspector)

    Returns:
        200: List of inspections
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        inspector_id = request.args.get('inspector_id', type=int)
        
        # Get inspections
        inspections, total = InspectionService.list_inspections(
            limit=limit,
            offset=offset,
            status=status,
            inspector_id=inspector_id
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
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@inspections_bp.route('/search', methods=['GET'])
@jwt_required()
def search_inspections():
    """
    Search inspections by property designation or notes.

    Query Parameters:
        - q: str (search term, required)
        - limit: int (default 50, max 100)
        - offset: int (default 0)
        - inspector_id: int (optional, filter by inspector)

    Returns:
        200: Search results
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
        inspector_id = request.args.get('inspector_id', type=int)
        
        # Search
        inspections, total = InspectionService.search_inspections(
            search_term=search_term,
            limit=limit,
            offset=offset,
            inspector_id=inspector_id
        )
        
        # Build response
        response = InspectionList(
            data=[InspectionResponse.model_validate(i) for i in inspections],
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


@inspections_bp.route('/<int:inspection_id>', methods=['GET'])
@jwt_required()
def get_inspection(inspection_id):
    """
    Get inspection by ID.

    Path Parameters:
        - inspection_id: int

    Returns:
        200: Inspection data
        404: Inspection not found
    """
    try:
        inspection_obj = InspectionService.get_inspection(inspection_id)
        response = InspectionResponse.model_validate(inspection_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@inspections_bp.route('/<int:inspection_id>/summary', methods=['GET'])
@jwt_required()
def get_inspection_summary(inspection_id):
    """
    Get comprehensive inspection summary.

    Path Parameters:
        - inspection_id: int

    Returns:
        200: Summary with apartment and defect counts
        404: Inspection not found
    """
    try:
        summary = InspectionService.get_inspection_summary(inspection_id)
        return jsonify(StandardResponse(data=summary).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# UPDATE
# =============================================================================

@inspections_bp.route('/<int:inspection_id>', methods=['PUT'])
@jwt_required()
@rate_limit("20/minute")
def update_inspection(inspection_id):
    """
    Update inspection with optimistic locking.

    Path Parameters:
        - inspection_id: int

    Request Body (InspectionUpdate):
        {
            "base_revision": 1,
            "date": "2026-02-04",
            "notes": "Updated notes",
            ...
        }

    Returns:
        200: Updated inspection
        400: Validation error
        404: Inspection not found
        409: Revision conflict
    """
    try:
        # Validate request body
        data = InspectionUpdate(**request.get_json())
        
        # Update inspection
        inspection_obj = InspectionService.update_inspection(
            inspection_id=inspection_id,
            data=data.model_dump(exclude={'base_revision'}, exclude_none=True),
            base_revision=data.base_revision
        )
        
        # Return response
        response = InspectionResponse.model_validate(inspection_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@inspections_bp.route('/<int:inspection_id>/status', methods=['PATCH'])
@jwt_required()
@rate_limit("20/minute")
def change_status(inspection_id):
    """
    Change inspection status (draft -> final -> archived).

    Path Parameters:
        - inspection_id: int

    Request Body:
        {
            "status": "final",
            "base_revision": 1
        }

    Returns:
        200: Updated inspection
        400: Invalid status transition
        404: Inspection not found
        409: Revision conflict
    """
    try:
        data = request.get_json()
        new_status = data.get('status')
        base_revision = data.get('base_revision')
        
        if not new_status or base_revision is None:
            return jsonify(ErrorResponse.validation_error(
                "Both 'status' and 'base_revision' are required"
            ).model_dump()), 400
        
        # Change status
        inspection_obj = InspectionService.change_status(
            inspection_id=inspection_id,
            new_status=new_status,
            base_revision=base_revision
        )
        
        # Return response
        response = InspectionResponse.model_validate(inspection_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@inspections_bp.route('/<int:inspection_id>/timer', methods=['PATCH'])
@jwt_required()
@rate_limit("60/minute")  # Higher rate limit for timer updates
def update_timer(inspection_id):
    """
    Update active time (used by timer).

    Path Parameters:
        - inspection_id: int

    Request Body:
        {
            "active_time_seconds": 3600,
            "base_revision": 1
        }

    Returns:
        200: Updated inspection
        400: Validation error
        404: Inspection not found
        409: Revision conflict
    """
    try:
        data = request.get_json()
        active_time_seconds = data.get('active_time_seconds')
        base_revision = data.get('base_revision')
        
        if active_time_seconds is None or base_revision is None:
            return jsonify(ErrorResponse.validation_error(
                "Both 'active_time_seconds' and 'base_revision' are required"
            ).model_dump()), 400
        
        # Update active time
        inspection_obj = InspectionService.update_active_time(
            inspection_id=inspection_id,
            active_time_seconds=active_time_seconds,
            base_revision=base_revision
        )
        
        # Return response
        response = InspectionResponse.model_validate(inspection_obj)
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

@inspections_bp.route('/<int:inspection_id>', methods=['DELETE'])
@jwt_required()
@rate_limit("10/minute")
def delete_inspection(inspection_id):
    """
    Soft delete inspection.

    Path Parameters:
        - inspection_id: int

    Returns:
        200: Inspection deleted
        400: Cannot delete (wrong status or has apartments)
        404: Inspection not found
    """
    try:
        # Check if can delete
        can_delete, reason = InspectionService.can_delete(inspection_id)
        if not can_delete:
            return jsonify(ErrorResponse.validation_error(reason).model_dump()), 400
        
        # Delete inspection
        deleted = InspectionService.delete_inspection(inspection_id)
        
        if deleted:
            return jsonify(StandardResponse(
                data={'message': 'Inspection deleted successfully'}
            ).model_dump()), 200
        else:
            return jsonify(StandardResponse(
                data={'message': 'Inspection already deleted'}
            ).model_dump()), 200
            
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# STATISTICS
# =============================================================================

@inspections_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    Get inspection statistics.

    Query Parameters:
        - inspector_id: int (optional, filter by inspector)

    Returns:
        200: Statistics data
    """
    try:
        inspector_id = request.args.get('inspector_id', type=int)
        stats = InspectionService.get_statistics(inspector_id=inspector_id)
        return jsonify(StandardResponse(data=stats).model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@inspections_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(ErrorResponse.not_found().model_dump()), 404


@inspections_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify(ErrorResponse.internal_error().model_dump()), 500