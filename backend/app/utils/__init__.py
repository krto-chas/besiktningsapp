"""
=============================================================================
BESIKTNINGSAPP BACKEND - UTILS PACKAGE
=============================================================================
Utility functions and helpers.

Available utilities:
- validators: Custom validation functions
- decorators: Auth decorators, rate limiting
- errors: Custom exception classes
- responses: Standard API response helpers
- logger: Logging configuration
- helpers: Miscellaneous helper functions
"""

from app.utils.validators import validate_uuid, validate_revision
from app.utils.decorators import jwt_required_with_user, admin_required
from app.utils.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
)
from app.utils.responses import success_response, error_response, paginated_response

__all__ = [
    "validate_uuid",
    "validate_revision",
    "jwt_required_with_user",
    "admin_required",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "success_response",
    "error_response",
    "paginated_response",
]
