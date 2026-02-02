"""
=============================================================================
BESIKTNINGSAPP BACKEND - DECORATORS
=============================================================================
Custom decorators for authentication, authorization, and rate limiting.
"""

from functools import wraps
from typing import Callable

from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models import User
from app.utils.errors import UnauthorizedError, ForbiddenError


def jwt_required_with_user(fn: Callable) -> Callable:
    """
    JWT required decorator that also loads user into g.current_user.
    
    Usage:
        @jwt_required_with_user
        def my_endpoint():
            user = g.current_user
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = User.query.get(user_id)
        if not user or not user.active:
            raise UnauthorizedError("Invalid or inactive user")
        
        g.current_user = user
        return fn(*args, **kwargs)
    
    return wrapper


def admin_required(fn: Callable) -> Callable:
    """
    Require admin role.
    
    Must be used with @jwt_required_with_user.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            raise UnauthorizedError("Authentication required")
        
        if g.current_user.role != 'admin':
            raise ForbiddenError("Admin access required")
        
        return fn(*args, **kwargs)
    
    return wrapper


def validate_revision_header(fn: Callable) -> Callable:
    """
    Validate X-Base-Revision header for optimistic locking.
    
    Adds base_revision to kwargs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        base_revision = request.headers.get('X-Base-Revision')
        
        if base_revision:
            try:
                kwargs['base_revision'] = int(base_revision)
            except ValueError:
                return jsonify({
                    "error": {
                        "code": "invalid_revision",
                        "message": "X-Base-Revision must be an integer"
                    }
                }), 400
        
        return fn(*args, **kwargs)
    
    return wrapper


def require_idempotency_key(fn: Callable) -> Callable:
    """
    Require X-Idempotency-Key header.
    
    Adds idempotency_key to kwargs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        idempotency_key = request.headers.get('X-Idempotency-Key')
        
        if not idempotency_key:
            return jsonify({
                "error": {
                    "code": "idempotency_key_required",
                    "message": "X-Idempotency-Key header is required"
                }
            }), 400
        
        kwargs['idempotency_key'] = idempotency_key
        return fn(*args, **kwargs)
    
    return wrapper
