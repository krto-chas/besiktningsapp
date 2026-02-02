"""Defect CRUD endpoints."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from pydantic import ValidationError
from app.extensions import db
from app.models import Defect, Apartment
from app.schemas import DefectCreate, DefectUpdate, DefectResponse, ErrorResponse

bp = Blueprint("defects", __name__)

@bp.route("", methods=["GET"])
@jwt_required()
def list_defects():
    try:
        apartment_id = request.args.get("apartment_id", type=int)
        query = Defect.query
        if apartment_id:
            query = query.filter_by(apartment_id=apartment_id)
        defects = query.all()
        return jsonify({"data": [DefectResponse.from_orm(d).dict() for d in defects]}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:defect_id>", methods=["GET"])
@jwt_required()
def get_defect(defect_id: int):
    try:
        defect = Defect.query.get(defect_id)
        if not defect:
            return jsonify(ErrorResponse.not_found().dict()), 404
        return jsonify({"data": DefectResponse.from_orm(defect).dict()}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("", methods=["POST"])
@jwt_required()
def create_defect():
    try:
        data = DefectCreate(**request.get_json())
        apartment_id = data.apartment_id
        if not apartment_id and data.apartment_client_id:
            apt = Apartment.query.filter_by(client_id=data.apartment_client_id).first()
            if apt:
                apartment_id = apt.id
        if not apartment_id:
            return jsonify(ErrorResponse.validation_error("apartment_id required").dict()), 400
        
        defect = Defect(
            client_id=data.client_id,
            apartment_id=apartment_id,
            room_index=data.room_index,
            code=data.code,
            title=data.title,
            description=data.description,
            remedy=data.remedy,
            severity=data.severity,
        )
        db.session.add(defect)
        db.session.commit()
        return jsonify({"data": DefectResponse.from_orm(defect).dict()}), 201
    except ValidationError:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:defect_id>", methods=["PATCH"])
@jwt_required()
def update_defect(defect_id: int):
    try:
        data = DefectUpdate(**request.get_json())
        defect = Defect.query.get(defect_id)
        if not defect:
            return jsonify(ErrorResponse.not_found().dict()), 404
        if defect.revision != data.base_revision:
            return jsonify(ErrorResponse.conflict().dict()), 409
        if data.room_index is not None: defect.room_index = data.room_index
        if data.code is not None: defect.code = data.code
        if data.title is not None: defect.title = data.title
        if data.description is not None: defect.description = data.description
        if data.remedy is not None: defect.remedy = data.remedy
        if data.severity is not None: defect.severity = data.severity
        db.session.commit()
        return jsonify({"data": DefectResponse.from_orm(defect).dict()}), 200
    except ValidationError:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:defect_id>", methods=["DELETE"])
@jwt_required()
def delete_defect(defect_id: int):
    try:
        defect = Defect.query.get(defect_id)
        if not defect:
            return jsonify(ErrorResponse.not_found().dict()), 404
        db.session.delete(defect)
        db.session.commit()
        return "", 204
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500
