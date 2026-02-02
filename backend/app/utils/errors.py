"""
=============================================================================
BESIKTNINGSAPP BACKEND - ERRORS
=============================================================================
Custom exception classes for API errors.
"""


class APIError(Exception):
    """Base API error class."""
    
    def __init__(self, message: str, status_code: int = 500, payload: dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
    
    def to_dict(self):
        """Convert to dict for JSON response."""
        rv = dict(self.payload)
        rv['message'] = self.message
        return rv


class ValidationError(APIError):
    """Validation error (400 Bad Request)."""
    
    def __init__(self, message: str = "Validation failed", field_errors: list = None):
        super().__init__(message, status_code=400)
        self.field_errors = field_errors or []


class UnauthorizedError(APIError):
    """Unauthorized error (401)."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(APIError):
    """Forbidden error (403)."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(APIError):
    """Not found error (404)."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(APIError):
    """Conflict error (409) - typically for revision mismatches."""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(message, status_code=409, payload=details or {})


class RateLimitError(APIError):
    """Rate limit exceeded error (429)."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
