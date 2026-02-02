"""Measurement CRUD endpoints."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from pydantic import ValidationError
from app.extensions import db
from app.models import Measurement, Inspection
from app.schemas import MeasurementCreate, MeasurementUpdate, MeasurementResponse, ErrorResponse

bp = Blueprint("measurements", __name__)

@bp.route("", methods=["GET"])
@jwt_required()
def list_measurements():
    try:
        inspection_id = request.args.get("inspection_id", type=int)
        query = Measurement.query
        if inspection_id:
            query = query.filter_by(inspection_id=inspection_id)
        measurements = query.all()
        return jsonify({"data": [MeasurementResponse.from_orm(m).dict() for m in measurements]}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:measurement_id>", methods=["GET"])
@jwt_required()
def get_measurement(measurement_id: int):
    try:
        measurement = Measurement.query.get(measurement_id)
        if not measurement:
            return jsonify(ErrorResponse.not_found().dict()), 404
        return jsonify({"data": MeasurementResponse.from_orm(measurement).dict()}), 200
    except Exception as e:
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("", methods=["POST"])
@jwt_required()
def create_measurement():
    try:
        data = MeasurementCreate(**request.get_json())
        inspection_id = data.inspection_id
        if not inspection_id and data.inspection_client_id:
            insp = Inspection.query.filter_by(client_id=data.inspection_client_id).first()
            if insp:
                inspection_id = insp.id
        if not inspection_id:
            return jsonify(ErrorResponse.validation_error("inspection_id required").dict()), 400
        
        measurement = Measurement(
            client_id=data.client_id,
            inspection_id=inspection_id,
            type=data.type,
            value=data.value,
            unit=data.unit,
            apartment_number=data.apartment_number,
            sort_key=data.sort_key,
            notes=data.notes,
        )
        db.session.add(measurement)
        db.session.commit()
        return jsonify({"data": MeasurementResponse.from_orm(measurement).dict()}), 201
    except ValidationError:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:measurement_id>", methods=["PATCH"])
@jwt_required()
def update_measurement(measurement_id: int):
    try:
        data = MeasurementUpdate(**request.get_json())
        measurement = Measurement.query.get(measurement_id)
        if not measurement:
            return jsonify(ErrorResponse.not_found().dict()), 404
        if measurement.revision != data.base_revision:
            return jsonify(ErrorResponse.conflict().dict()), 409
        if data.type: measurement.type = data.type
        if data.value is not None: measurement.value = data.value
        if data.unit: measurement.unit = data.unit
        if data.apartment_number is not None: measurement.apartment_number = data.apartment_number
        if data.sort_key is not None: measurement.sort_key = data.sort_key
        if data.notes is not None: measurement.notes = data.notes
        db.session.commit()
        return jsonify({"data": MeasurementResponse.from_orm(measurement).dict()}), 200
    except ValidationError:
        return jsonify(ErrorResponse.validation_error().dict()), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500

@bp.route("/<int:measurement_id>", methods=["DELETE"])
@jwt_required()
def delete_measurement(measurement_id: int):
    try:
        measurement = Measurement.query.get(measurement_id)
        if not measurement:
            return jsonify(ErrorResponse.not_found().dict()), 404
        db.session.delete(measurement)
        db.session.commit()
        return "", 204
    except Exception as e:
        db.session.rollback()
        return jsonify(ErrorResponse.internal_error().dict()), 500
