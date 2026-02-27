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
from app.utils.decorators import (
    rate_limit,
    require_role,
    require_admin,
    require_inspector_or_admin,
    log_request,
    validate_json,
    api_endpoint,
)
from app.utils.errors import (
    BesiktningsappError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    StorageError,
    PDFGenerationError,
    SyncError,
)
from app.utils.responses import success_response, error_response, paginated_response

__all__ = [
    # Validators
    "validate_uuid",
    "validate_revision",
    # Decorators
    "rate_limit",
    "require_role",
    "require_admin",
    "require_inspector_or_admin",
    "log_request",
    "validate_json",
    "api_endpoint",
    # Errors
    "BesiktningsappError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitError",
    "StorageError",
    "PDFGenerationError",
    "SyncError",
    # Responses
    "success_response",
    "error_response",
    "paginated_response",
]
