"""
=============================================================================
BESIKTNINGSAPP BACKEND - DECORATORS
=============================================================================
Custom decorators for authentication, authorization, and rate limiting.

Decorators:
- rate_limit: Rate limiting decorator
- require_role: Role-based access control
- log_request: Request logging
"""
from functools import wraps
from flask import request, jsonify, current_app, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time

from app.utils.errors import ForbiddenError, RateLimitError


# =============================================================================
# RATE LIMITING
# =============================================================================

def rate_limit(limit_string: str):
    """
    Rate limiting decorator.
    
    Args:
        limit_string: Limit format (e.g., "10/minute", "100/hour")
    
    Usage:
        @rate_limit("10/minute")
        def my_endpoint():
            ...
    
    Note:
        This is a placeholder that integrates with Flask-Limiter.
        The actual rate limiting is configured in extensions.py.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting is handled by Flask-Limiter in extensions.py
            # This decorator just adds metadata
            if not hasattr(f, '_rate_limit'):
                f._rate_limit = limit_string
            return f(*args, **kwargs)
        
        # Store limit info for documentation
        decorated_function._rate_limit = limit_string
        return decorated_function
    
    return decorator


# =============================================================================
# ROLE-BASED ACCESS CONTROL
# =============================================================================

def require_role(*allowed_roles):
    """
    Require user to have specific role(s).
    
    Args:
        *allowed_roles: Variable number of allowed roles
    
    Usage:
        @require_role('admin')
        def admin_only_endpoint():
            ...
        
        @require_role('admin', 'inspector')
        def multi_role_endpoint():
            ...
    
    Raises:
        ForbiddenError: If user doesn't have required role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT exists
            verify_jwt_in_request()
            
            # Get user claims from JWT
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Check if user has required role
            if user_role not in allowed_roles:
                raise ForbiddenError(
                    f"Access denied. Required role: {', '.join(allowed_roles)}",
                    required_role=', '.join(allowed_roles)
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_admin(f):
    """
    Shortcut decorator to require admin role.
    
    Usage:
        @require_admin
        def admin_endpoint():
            ...
    """
    return require_role('admin')(f)


def require_inspector_or_admin(f):
    """
    Shortcut decorator to require inspector or admin role.
    
    Usage:
        @require_inspector_or_admin
        def inspector_endpoint():
            ...
    """
    return require_role('inspector', 'admin')(f)


# =============================================================================
# RESOURCE OWNERSHIP
# =============================================================================

def require_owner(resource_getter, resource_id_param='resource_id'):
    """
    Require user to be the owner of the resource.
    
    Args:
        resource_getter: Function that takes resource_id and returns resource
        resource_id_param: Name of the parameter containing resource ID
    
    Usage:
        @require_owner(PropertyService.get_property, 'property_id')
        def update_property(property_id):
            ...
    
    Raises:
        ForbiddenError: If user is not the owner
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT exists
            verify_jwt_in_request()
            
            # Get current user ID
            user_id = get_jwt_identity()
            
            # Get user role
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Admins can access everything
            if user_role == 'admin':
                return f(*args, **kwargs)
            
            # Get resource ID from kwargs
            resource_id = kwargs.get(resource_id_param)
            
            if resource_id is None:
                raise ValueError(f"Parameter '{resource_id_param}' not found in function arguments")
            
            # Get resource
            resource = resource_getter(resource_id)
            
            # Check ownership
            owner_id = getattr(resource, 'created_by_id', None) or \
                      getattr(resource, 'inspector_id', None) or \
                      getattr(resource, 'uploaded_by_id', None)
            
            if owner_id != user_id:
                raise ForbiddenError("Access denied. You don't own this resource.")
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# =============================================================================
# REQUEST LOGGING
# =============================================================================

def log_request(include_body=False):
    """
    Log incoming request details.
    
    Args:
        include_body: Whether to log request body (default False for security)
    
    Usage:
        @log_request(include_body=True)
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Start timing
            g.start_time = time.time()
            
            # Log request
            current_app.logger.info(
                f"Request: {request.method} {request.path} "
                f"[Request-ID: {g.get('request_id', 'N/A')}]"
            )
            
            if include_body and request.is_json:
                current_app.logger.debug(f"Request body: {request.get_json()}")
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Log response
            elapsed = time.time() - g.start_time
            status_code = response[1] if isinstance(response, tuple) else 200
            
            current_app.logger.info(
                f"Response: {status_code} [Request-ID: {g.get('request_id', 'N/A')}] "
                f"({elapsed:.3f}s)"
            )
            
            return response
        
        return decorated_function
    
    return decorator


# =============================================================================
# VALIDATION
# =============================================================================

def validate_json(*required_fields):
    """
    Validate that request contains JSON with required fields.
    
    Args:
        *required_fields: Variable number of required field names
    
    Usage:
        @validate_json('email', 'password')
        def login():
            ...
    
    Raises:
        ValidationError: If JSON invalid or fields missing
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.utils.errors import ValidationError
            
            # Check if request has JSON
            if not request.is_json:
                raise ValidationError("Request must be JSON")
            
            # Get JSON data
            data = request.get_json()
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# =============================================================================
# CACHING
# =============================================================================

def cache_response(timeout=300):
    """
    Cache endpoint response.
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
    
    Usage:
        @cache_response(timeout=600)
        def expensive_query():
            ...
    
    Note:
        Requires Redis configured for caching.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only cache GET requests
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Build cache key
            cache_key = f"cache:{request.path}:{request.query_string.decode()}"
            
            # Try to get from cache
            try:
                from app.extensions import cache
                cached = cache.get(cache_key)
                
                if cached:
                    current_app.logger.debug(f"Cache hit: {cache_key}")
                    return cached
            except Exception as e:
                current_app.logger.warning(f"Cache get failed: {e}")
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Store in cache
            try:
                from app.extensions import cache
                cache.set(cache_key, response, timeout=timeout)
                current_app.logger.debug(f"Cache set: {cache_key}")
            except Exception as e:
                current_app.logger.warning(f"Cache set failed: {e}")
            
            return response
        
        return decorated_function
    
    return decorator


# =============================================================================
# REQUEST ID TRACKING
# =============================================================================

def track_request_id(f):
    """
    Add request ID to Flask's g object for tracking.
    
    Usage:
        @track_request_id
        def my_endpoint():
            request_id = g.request_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import uuid
        
        # Get or generate request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.request_id = request_id
        
        # Execute function
        response = f(*args, **kwargs)
        
        # Add request ID to response headers
        if isinstance(response, tuple):
            data, status_code = response
            return data, status_code, {'X-Request-ID': request_id}
        else:
            return response, {'X-Request-ID': request_id}
    
    return decorated_function


# =============================================================================
# ERROR HANDLING
# =============================================================================

def handle_errors(f):
    """
    Catch and properly format errors.
    
    Usage:
        @handle_errors
        def my_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.utils.errors import BesiktningsappError
        from app.schemas import ErrorResponse
        
        try:
            return f(*args, **kwargs)
        except BesiktningsappError as e:
            # Custom errors are already properly formatted
            raise
        except Exception as e:
            # Log unexpected errors
            current_app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            
            # Return generic error response
            return jsonify(ErrorResponse.internal_error().model_dump()), 500
    
    return decorated_function


# =============================================================================
# COMBINED DECORATORS
# =============================================================================

def api_endpoint(limit: str = None, roles: tuple = None, log: bool = True):
    """
    Combined decorator for common API endpoint needs.
    
    Args:
        limit: Rate limit string (e.g., "10/minute")
        roles: Tuple of allowed roles
        log: Whether to log requests (default True)
    
    Usage:
        @api_endpoint(limit="10/minute", roles=('admin',), log=True)
        def my_endpoint():
            ...
    """
    def decorator(f):
        # Apply decorators in reverse order
        decorated = f
        
        if log:
            decorated = log_request()(decorated)
        
        if roles:
            decorated = require_role(*roles)(decorated)
        
        if limit:
            decorated = rate_limit(limit)(decorated)
        
        decorated = handle_errors(decorated)
        decorated = track_request_id(decorated)
        
        return decorated
    
    return decorator