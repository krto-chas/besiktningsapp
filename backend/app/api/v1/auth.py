"""
=============================================================================
BESIKTNINGSAPP BACKEND - AUTH ENDPOINTS
=============================================================================
Authentication endpoints: /auth/login, /auth/me
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.extensions import db, limiter
from app.models import User
from app.schemas import LoginRequest, UserProfile, ErrorResponse

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
@limiter.limit("5/minute")
def login():
    """
    User login endpoint.
    
    Request:
        POST /api/v1/auth/login
        Content-Type: application/json
        Body: {"email": "user@example.com", "password": "password"}
    
    Response:
        200 OK: {
            "data": {
                "access_token": "...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {...}
            }
        }
        400 Bad Request: Invalid request format
        401 Unauthorized: Invalid credentials
        429 Too Many Requests: Rate limit exceeded
    """
    try:
        # Validate request
        data = LoginRequest(**request.get_json())
        
        # Find user
        user = User.query.filter_by(email=data.email).first()
        
        if not user:
            return jsonify(ErrorResponse.unauthorized("Invalid email or password").dict()), 401
        
        # Check password
        if not user.check_password(data.password):
            return jsonify(ErrorResponse.unauthorized("Invalid email or password").dict()), 401
        
        # Check if active
        if not user.active:
            return jsonify(ErrorResponse.forbidden("Account is inactive").dict()), 403
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        # Get token expiration from config
        from flask import current_app
        expires_in = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
        
        # Build response
        response = {
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": expires_in,
                "user": UserProfile.from_orm(user).dict()
            }
        }
        
        return jsonify(response), 200
        
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "issue": err["msg"]} for err in e.errors()]
        return jsonify(ErrorResponse.validation_error(field_errors=errors).dict()), 400
    
    except Exception as e:
        current_app.logger.exception(f"Login error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    Get current user profile.
    
    Request:
        GET /api/v1/auth/me
        Authorization: Bearer <token>
    
    Response:
        200 OK: {
            "data": {
                "id": 1,
                "email": "user@example.com",
                "name": "User Name",
                ...
            }
        }
        401 Unauthorized: Invalid or missing token
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        # Find user
        user = User.query.get(user_id)
        
        if not user:
            return jsonify(ErrorResponse.not_found("User not found").dict()), 404
        
        # Return user profile
        return jsonify({
            "data": UserProfile.from_orm(user).dict()
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Get current user error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500


@bp.route("/refresh", methods=["POST"])
@jwt_required()
def refresh_token():
    """
    Refresh access token.
    
    Request:
        POST /api/v1/auth/refresh
        Authorization: Bearer <token>
    
    Response:
        200 OK: {
            "data": {
                "access_token": "...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user = User.query.get(user_id)
        
        if not user or not user.active:
            return jsonify(ErrorResponse.unauthorized("Invalid token").dict()), 401
        
        # Create new access token
        access_token = create_access_token(identity=user_id)
        
        # Get token expiration
        from flask import current_app
        expires_in = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
        
        return jsonify({
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": expires_in
            }
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Token refresh error: {e}")
        return jsonify(ErrorResponse.internal_error().dict()), 500
