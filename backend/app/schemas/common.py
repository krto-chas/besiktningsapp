"""
=============================================================================
BESIKTNINGSAPP BACKEND - COMMON SCHEMAS
=============================================================================
Common/shared Pydantic schemas used across the application.

Includes:
- Pagination schemas (offset and cursor-based)
- Standard response wrappers
- Error response formats
- Field validation errors
"""
from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime

from pydantic import BaseModel, Field, validator


# =============================================================================
# PAGINATION
# =============================================================================

class PaginationParams(BaseModel):
    """Standard offset-based pagination parameters."""
    
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of items to return (1-100)",
    )
    
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip",
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""
    
    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for pagination (opaque string)",
    )
    
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of items to return (1-100)",
    )


class PaginationMeta(BaseModel):
    """Pagination metadata for responses."""
    
    total: Optional[int] = Field(
        default=None,
        description="Total number of items (if available)",
    )
    
    limit: int = Field(
        description="Number of items per page",
    )
    
    offset: Optional[int] = Field(
        default=None,
        description="Current offset (offset-based pagination)",
    )
    
    cursor: Optional[str] = Field(
        default=None,
        description="Next cursor (cursor-based pagination)",
    )
    
    has_more: bool = Field(
        default=False,
        description="Whether there are more items available",
    )


# =============================================================================
# STANDARD RESPONSES
# =============================================================================

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    
    data: T = Field(
        description="Response data",
    )
    
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {"id": 1, "name": "Example"},
                "meta": {"timestamp": "2026-01-29T12:00:00Z"}
            }
        }


# =============================================================================
# ERROR RESPONSES
# =============================================================================

class FieldError(BaseModel):
    """Field-level validation error."""
    
    field: str = Field(
        description="Field name that failed validation",
    )
    
    issue: str = Field(
        description="Description of the validation issue",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "field": "email",
                "issue": "Invalid email format"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: Dict[str, Any] = Field(
        description="Error information",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request",
                    "field_errors": [
                        {"field": "email", "issue": "Invalid email format"}
                    ]
                }
            }
        }
    
    @classmethod
    def validation_error(
        cls,
        message: str = "Invalid request",
        field_errors: Optional[List[FieldError]] = None,
    ) -> "ErrorResponse":
        """Create validation error response."""
        return cls(
            error={
                "code": "validation_error",
                "message": message,
                "field_errors": [e.dict() for e in (field_errors or [])],
            }
        )
    
    @classmethod
    def not_found(cls, message: str = "Resource not found") -> "ErrorResponse":
        """Create not found error response."""
        return cls(
            error={
                "code": "not_found",
                "message": message,
            }
        )
    
    @classmethod
    def unauthorized(cls, message: str = "Authentication required") -> "ErrorResponse":
        """Create unauthorized error response."""
        return cls(
            error={
                "code": "unauthorized",
                "message": message,
            }
        )
    
    @classmethod
    def forbidden(cls, message: str = "Access denied") -> "ErrorResponse":
        """Create forbidden error response."""
        return cls(
            error={
                "code": "forbidden",
                "message": message,
            }
        )
    
    @classmethod
    def conflict(
        cls,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ) -> "ErrorResponse":
        """Create conflict error response."""
        error_data = {
            "code": "conflict",
            "message": message,
        }
        if details:
            error_data["details"] = details
        return cls(error=error_data)
    
    @classmethod
    def internal_error(
        cls,
        message: str = "An internal error occurred"
    ) -> "ErrorResponse":
        """Create internal error response."""
        return cls(
            error={
                "code": "internal_server_error",
                "message": message,
            }
        )


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        """Pydantic config."""
        from_attributes = True
        populate_by_name = True
        str_strip_whitespace = True


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime = Field(
        description="Creation timestamp (UTC)",
    )
    
    updated_at: datetime = Field(
        description="Last update timestamp (UTC)",
    )


class RevisionMixin(BaseModel):
    """Mixin for revision tracking."""
    
    revision: int = Field(
        ge=1,
        description="Revision number for optimistic locking",
    )


class ClientIdMixin(BaseModel):
    """Mixin for client ID."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client-generated UUID (for offline-first sync)",
    )


# =============================================================================
# VALIDATORS
# =============================================================================

def validate_apartment_number(v: str) -> str:
    """
    Validate apartment number format.
    
    Allowed formats:
    - Numeric: "1201", "12"
    - Alphanumeric: "A12", "12B", "A1201"
    
    Args:
        v: Apartment number string
        
    Returns:
        Validated apartment number
        
    Raises:
        ValueError: If format is invalid
    """
    import re
    
    if not v:
        raise ValueError("Apartment number cannot be empty")
    
    # Pattern: optional letter + 1-5 digits + optional letter
    pattern = r'^[A-Za-z]?\d{1,5}[A-Za-z]?$'
    
    if not re.match(pattern, v):
        raise ValueError(
            "Apartment number must match pattern: "
            "[A-Z]?[0-9]{1,5}[A-Z]? (e.g., '1201', 'A12', '12B')"
        )
    
    return v


def validate_email(v: str) -> str:
    """
    Validate email format.
    
    Args:
        v: Email address
        
    Returns:
        Validated and normalized email
        
    Raises:
        ValueError: If email is invalid
    """
    import re
    
    if not v:
        raise ValueError("Email cannot be empty")
    
    # Simple email regex (RFC 5322 simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, v):
        raise ValueError("Invalid email format")
    
    return v.lower()


def validate_phone(v: Optional[str]) -> Optional[str]:
    """
    Validate phone number format.
    
    Args:
        v: Phone number (optional)
        
    Returns:
        Validated phone number or None
        
    Raises:
        ValueError: If phone format is invalid
    """
    if not v:
        return None
    
    # Remove common separators
    cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Check if it's a valid phone number (digits, +, and parentheses only)
    import re
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        raise ValueError("Invalid phone number format")
    
    return v
