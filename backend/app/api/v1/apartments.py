"""
=============================================================================
BESIKTNINGSAPP BACKEND - APARTMENTS API
=============================================================================
REST API endpoints for Apartment operations.

Endpoints:
- POST   /apartments           - Create apartment
- GET    /apartments           - List apartments
- GET    /apartments/:id       - Get apartment
- PUT    /apartments/:id       - Update apartment
- DELETE /apartments/:id       - Delete apartment
- GET    /apartments/:id/defects - Get apartment defects
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.inspection_service import InspectionService
from app.schemas import (
    ApartmentCreate,
    ApartmentUpdate,
    ApartmentResponse,
    ApartmentList,
    StandardResponse,
    ErrorResponse,
)
from app.utils.errors import NotFoundError, ConflictError, ValidationError
from app.utils.decorators import rate_limit
from app.models import Apartment, Defect
from app.extensions import db

apartments_bp = Blueprint('apartments', __name__, url_prefix='/apartments')


# =============================================================================
# CREATE
# =============================================================================

@apartments_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit("20/minute")
def create_apartment():
    """
    Create new apartment.

    Request Body (ApartmentCreate):
        {
            "inspection_id": 1,
            "apartment_number": "1201",
            "rooms": [
                {"index": 0, "type": "hall"},
                {"index": 1, "type": "kok"},
                {"index": 2, "type": "vardagsrum"}
            ],
            "notes": "3 rum och kök",
            "client_id": "optional-uuid"
        }

    Returns:
        201: Created apartment
        400: Validation error
        404: Inspection not found
        409: Duplicate client_id
    """
    try:
        # Validate request body
        data = ApartmentCreate(**request.get_json())
        
        # Verify inspection exists
        InspectionService.get_inspection(data.inspection_id)
        
        # Create apartment
        apartment_obj = Apartment(
            inspection_id=data.inspection_id,
            apartment_number=data.apartment_number,
            rooms=data.rooms,
            notes=data.notes,
            client_id=data.client_id,
            revision=1,
        )
        
        db.session.add(apartment_obj)
        db.session.commit()
        db.session.refresh(apartment_obj)
        
        # Return response
        response = ApartmentResponse.model_validate(apartment_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 201
        
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# READ
# =============================================================================

@apartments_bp.route('', methods=['GET'])
@jwt_required()
def list_apartments():
    """
    List apartments with pagination.

    Query Parameters:
        - limit: int (default 50, max 100)
        - offset: int (default 0)
        - inspection_id: int (optional, filter by inspection)

    Returns:
        200: List of apartments
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        inspection_id = request.args.get('inspection_id', type=int)
        
        # Build query
        query = Apartment.query.filter_by(deleted_at=None)
        
        if inspection_id:
            query = query.filter_by(inspection_id=inspection_id)
        
        # Get apartments
        total = query.count()
        apartments = query.order_by(
            Apartment.apartment_number
        ).limit(limit).offset(offset).all()
        
        # Build response
        response = ApartmentList(
            data=[ApartmentResponse.model_validate(a) for a in apartments],
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


@apartments_bp.route('/<int:apartment_id>', methods=['GET'])
@jwt_required()
def get_apartment(apartment_id):
    """
    Get apartment by ID.

    Path Parameters:
        - apartment_id: int

    Returns:
        200: Apartment data
        404: Apartment not found
    """
    try:
        apartment_obj = Apartment.query.filter_by(
            id=apartment_id,
            deleted_at=None
        ).first()
        
        if not apartment_obj:
            raise NotFoundError(f"Apartment with id {apartment_id} not found")
        
        response = ApartmentResponse.model_validate(apartment_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@apartments_bp.route('/<int:apartment_id>/defects', methods=['GET'])
@jwt_required()
def get_apartment_defects(apartment_id):
    """
    Get all defects for an apartment.

    Path Parameters:
        - apartment_id: int

    Query Parameters:
        - limit: int (default 50, max 100)
        - offset: int (default 0)

    Returns:
        200: List of defects
        404: Apartment not found
    """
    try:
        # Verify apartment exists
        apartment_obj = Apartment.query.filter_by(
            id=apartment_id,
            deleted_at=None
        ).first()
        
        if not apartment_obj:
            raise NotFoundError(f"Apartment with id {apartment_id} not found")
        
        # Parse pagination
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Get defects
        from app.schemas import DefectResponse, DefectList
        
        query = Defect.query.filter_by(
            apartment_id=apartment_id,
            deleted_at=None
        )
        
        total = query.count()
        defects = query.order_by(
            Defect.room_index,
            Defect.code
        ).limit(limit).offset(offset).all()
        
        # Build response
        response = DefectList(
            data=[DefectResponse.model_validate(d) for d in defects],
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

@apartments_bp.route('/<int:apartment_id>', methods=['PUT'])
@jwt_required()
@rate_limit("20/minute")
def update_apartment(apartment_id):
    """
    Update apartment with optimistic locking.

    Path Parameters:
        - apartment_id: int

    Request Body (ApartmentUpdate):
        {
            "base_revision": 1,
            "apartment_number": "1201A",
            "rooms": [...],
            "notes": "Updated notes"
        }

    Returns:
        200: Updated apartment
        400: Validation error
        404: Apartment not found
        409: Revision conflict
    """
    try:
        # Get apartment
        apartment_obj = Apartment.query.filter_by(
            id=apartment_id,
            deleted_at=None
        ).first()
        
        if not apartment_obj:
            raise NotFoundError(f"Apartment with id {apartment_id} not found")
        
        # Validate request body
        data = ApartmentUpdate(**request.get_json())
        
        # Check revision
        if apartment_obj.revision != data.base_revision:
            raise ConflictError(
                f"Revision conflict. Expected revision {data.base_revision}, "
                f"but current revision is {apartment_obj.revision}"
            )
        
        # Update fields
        if data.apartment_number is not None:
            apartment_obj.apartment_number = data.apartment_number
        if data.rooms is not None:
            apartment_obj.rooms = data.rooms
        if data.notes is not None:
            apartment_obj.notes = data.notes
        
        # Increment revision
        apartment_obj.revision += 1
        apartment_obj.updated_at = db.func.now()
        
        db.session.commit()
        db.session.refresh(apartment_obj)
        
        # Return response
        response = ApartmentResponse.model_validate(apartment_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ConflictError as e:
        return jsonify(ErrorResponse.conflict(str(e)).model_dump()), 409
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# DELETE
# =============================================================================

@apartments_bp.route('/<int:apartment_id>', methods=['DELETE'])
@jwt_required()
@rate_limit("10/minute")
def delete_apartment(apartment_id):
    """
    Soft delete apartment.

    Path Parameters:
        - apartment_id: int

    Returns:
        200: Apartment deleted
        400: Cannot delete (has defects)
        404: Apartment not found
    """
    try:
        # Get apartment
        apartment_obj = Apartment.query.filter_by(id=apartment_id).first()
        
        if not apartment_obj:
            raise NotFoundError(f"Apartment with id {apartment_id} not found")
        
        if apartment_obj.deleted_at:
            return jsonify(StandardResponse(
                data={'message': 'Apartment already deleted'}
            ).model_dump()), 200
        
        # Check if has defects
        defect_count = Defect.query.filter_by(
            apartment_id=apartment_id,
            deleted_at=None
        ).count()
        
        if defect_count > 0:
            return jsonify(ErrorResponse.validation_error(
                f"Cannot delete apartment. It has {defect_count} defect(s). Delete defects first."
            ).model_dump()), 400
        
        # Soft delete
        apartment_obj.deleted_at = db.func.now()
        apartment_obj.revision += 1
        
        db.session.commit()
        
        return jsonify(StandardResponse(
            data={'message': 'Apartment deleted successfully'}
        ).model_dump()), 200
            
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@apartments_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(ErrorResponse.not_found().model_dump()), 404


@apartments_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify(ErrorResponse.internal_error().model_dump()), 500