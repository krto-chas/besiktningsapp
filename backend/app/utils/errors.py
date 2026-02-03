"""
=============================================================================
BESIKTNINGSAPP BACKEND - CUSTOM EXCEPTIONS
=============================================================================
Custom exception classes for better error handling.

Exception Hierarchy:
- BesiktningsappError (base)
  - ValidationError (400)
  - NotFoundError (404)
  - ConflictError (409)
  - UnauthorizedError (401)
  - ForbiddenError (403)
  - RateLimitError (429)
  - StorageError (500)
"""


class BesiktningsappError(Exception):
    """Base exception for all custom errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        """
        Initialize exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        error_dict = {
            'code': self.__class__.__name__.replace('Error', '').lower(),
            'message': self.message,
        }
        
        if self.details:
            error_dict['details'] = self.details
        
        return error_dict


class ValidationError(BesiktningsappError):
    """
    Raised when validation fails.
    
    HTTP Status: 400 Bad Request
    
    Examples:
        - Invalid input data
        - Missing required fields
        - Format errors
        - Business rule violations
    """
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Optional field name that failed validation
            details: Additional error details
        """
        super().__init__(message, status_code=400, details=details)
        self.field = field
    
    def to_dict(self) -> dict:
        """Convert to dictionary with field info."""
        error_dict = super().to_dict()
        error_dict['code'] = 'validation_error'
        
        if self.field:
            error_dict['field'] = self.field
        
        return error_dict


class NotFoundError(BesiktningsappError):
    """
    Raised when resource not found.
    
    HTTP Status: 404 Not Found
    
    Examples:
        - Property ID doesn't exist
        - Inspection not found
        - Image not found
    """
    
    def __init__(self, message: str, resource_type: str = None, resource_id: any = None):
        """
        Initialize not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource (e.g., 'property', 'inspection')
            resource_id: ID of resource that wasn't found
        """
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id is not None:
            details['resource_id'] = resource_id
        
        super().__init__(message, status_code=404, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'not_found'
        return error_dict


class ConflictError(BesiktningsappError):
    """
    Raised when there's a conflict.
    
    HTTP Status: 409 Conflict
    
    Examples:
        - Optimistic locking (revision mismatch)
        - Duplicate client_id
        - Resource already exists
    """
    
    def __init__(
        self,
        message: str,
        expected_revision: int = None,
        actual_revision: int = None,
        details: dict = None
    ):
        """
        Initialize conflict error.
        
        Args:
            message: Error message
            expected_revision: Expected revision number
            actual_revision: Actual revision number
            details: Additional error details
        """
        conflict_details = details or {}
        
        if expected_revision is not None:
            conflict_details['expected_revision'] = expected_revision
        if actual_revision is not None:
            conflict_details['actual_revision'] = actual_revision
        
        super().__init__(message, status_code=409, details=conflict_details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'conflict'
        return error_dict


class UnauthorizedError(BesiktningsappError):
    """
    Raised when authentication fails.
    
    HTTP Status: 401 Unauthorized
    
    Examples:
        - Invalid credentials
        - Expired token
        - Missing authentication
    """
    
    def __init__(self, message: str = "Authentication required"):
        """Initialize unauthorized error."""
        super().__init__(message, status_code=401)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'unauthorized'
        return error_dict


class ForbiddenError(BesiktningsappError):
    """
    Raised when user lacks permission.
    
    HTTP Status: 403 Forbidden
    
    Examples:
        - Insufficient permissions
        - Access denied to resource
        - Role-based access control violation
    """
    
    def __init__(self, message: str = "Access denied", required_role: str = None):
        """
        Initialize forbidden error.
        
        Args:
            message: Error message
            required_role: Required role for this action
        """
        details = {}
        if required_role:
            details['required_role'] = required_role
        
        super().__init__(message, status_code=403, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'forbidden'
        return error_dict


class RateLimitError(BesiktningsappError):
    """
    Raised when rate limit exceeded.
    
    HTTP Status: 429 Too Many Requests
    
    Examples:
        - Too many requests in time window
        - Upload quota exceeded
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        limit: str = None
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
            limit: Rate limit description (e.g., "10/minute")
        """
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        if limit:
            details['limit'] = limit
        
        super().__init__(message, status_code=429, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'rate_limit_exceeded'
        return error_dict


class StorageError(BesiktningsappError):
    """
    Raised when storage operation fails.
    
    HTTP Status: 500 Internal Server Error
    
    Examples:
        - S3 upload failed
        - File system error
        - Storage quota exceeded
    """
    
    def __init__(self, message: str, operation: str = None):
        """
        Initialize storage error.
        
        Args:
            message: Error message
            operation: Storage operation that failed (e.g., 'upload', 'delete')
        """
        details = {}
        if operation:
            details['operation'] = operation
        
        super().__init__(message, status_code=500, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'storage_error'
        return error_dict


class PDFGenerationError(BesiktningsappError):
    """
    Raised when PDF generation fails.
    
    HTTP Status: 500 Internal Server Error
    
    Examples:
        - WeasyPrint error
        - Template not found
        - Invalid template data
    """
    
    def __init__(self, message: str, template: str = None):
        """
        Initialize PDF generation error.
        
        Args:
            message: Error message
            template: Template name that caused the error
        """
        details = {}
        if template:
            details['template'] = template
        
        super().__init__(message, status_code=500, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'pdf_generation_error'
        return error_dict


class SyncError(BesiktningsappError):
    """
    Raised when sync operation fails.
    
    HTTP Status: 500 Internal Server Error
    
    Examples:
        - Sync conflict resolution failed
        - Invalid sync data
        - Sync integrity violation
    """
    
    def __init__(self, message: str, operation: str = None):
        """
        Initialize sync error.
        
        Args:
            message: Error message
            operation: Sync operation that failed (e.g., 'push', 'pull')
        """
        details = {}
        if operation:
            details['operation'] = operation
        
        super().__init__(message, status_code=500, details=details)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        error_dict = super().to_dict()
        error_dict['code'] = 'sync_error'
        return error_dict


# =============================================================================
# ERROR HANDLER HELPERS
# =============================================================================

def register_error_handlers(app):
    """
    Register error handlers for Flask app.
    
    Args:
        app: Flask application instance
    """
    from flask import jsonify
    
    @app.errorhandler(BesiktningsappError)
    def handle_custom_error(error):
        """Handle custom exceptions."""
        response = jsonify({'error': error.to_dict()})
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 Not Found."""
        return jsonify({
            'error': {
                'code': 'not_found',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def handle_500(error):
        """Handle 500 Internal Server Error."""
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An internal error occurred'
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle uncaught exceptions."""
        app.logger.error(f"Uncaught exception: {str(error)}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred'
            }
        }), 500