"""Apartment CRUD endpoints."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from pydantic import ValidationError
from app.extensions import db
from app.models import Apartment, Inspection
from app.schemas import ApartmentCreate, ApartmentUpdate, ApartmentResponse, ErrorResponse

bp = Blueprint("apartments", __name__)

@bp.route("", methods=["GET"])
@jwt_required()
def list_apartments():
    try:
        inspection_id = request.args.get("inspection_id", type=int)
        query = Apartment.query
        if inspection_id:
            query = query.filter_by(inspection_id=inspection_id)
        apartments = query.all()
        return jsonify({"data": [ApartmentResponse.from_orm(a).dict() for a in apartments]}), 200
    except Exception as e:
        current_app.logger.exception(f"List apartments error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:apartment_id>", methods=["GET"])
@jwt_required()
def get_apartment(apartment_id: int):
    try:
        apartment = Apartment.query.get(apartment_id)
        if not apartment:
            return jsonify(ErrorResponse.not_found().dict()), 404
        return jsonify({"data": ApartmentResponse.from_orm(apartment).dict()}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("", methods=["POST"])
@jwt_required()
def create_apartment():
    try:
        data = ApartmentCreate(**request.get_json())
        inspection_id = data.inspection_id
        if not inspection_id and data.inspection_client_id:
            insp = Inspection.query.filter_by(client_id=data.inspection_client_id).first()
            if insp:
                inspection_id = insp.id
        if not inspection_id:
            return jsonify(ErrorResponse.validation_error("inspection_id required").dict()), 400
        
        apartment = Apartment(
            client_id=data.client_id,
            inspection_id=inspection_id,
            apartment_number=data.apartment_number,
            rooms=[r.dict() for r in data.rooms],
            notes=data.notes,
        )
        db.session.add(apartment)
        db.session.commit()
        return jsonify({"data": ApartmentResponse.from_orm(apartment).dict()}), 201
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Create apartment error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:apartment_id>", methods=["PATCH"])
@jwt_required()
def update_apartment(apartment_id: int):
    try:
        data = ApartmentUpdate(**request.get_json())
        apartment = Apartment.query.get(apartment_id)
        if not apartment:
            return jsonify(ErrorResponse.not_found().dict()), 404
        if apartment.revision != data.base_revision:
            return jsonify(ErrorResponse.conflict().dict()), 409
        if data.apartment_number: apartment.apartment_number = data.apartment_number
        if data.rooms is not None: apartment.rooms = [r.dict() for r in data.rooms]
        if data.notes is not None: apartment.notes = data.notes
        db.session.commit()
        return jsonify({"data": ApartmentResponse.from_orm(apartment).dict()}), 200
    except ValidationError:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:apartment_id>", methods=["DELETE"])
@jwt_required()
def delete_apartment(apartment_id: int):
    try:
        apartment = Apartment.query.get(apartment_id)
        if not apartment:
            return jsonify(ErrorResponse.not_found().dict()), 404
        db.session.delete(apartment)
        db.session.commit()
        return "", 204
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500
