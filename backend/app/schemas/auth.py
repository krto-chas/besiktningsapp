"""
=============================================================================
BESIKTNINGSAPP BACKEND - AUTH SCHEMAS
=============================================================================
Pydantic schemas for authentication and authorization.
"""
from __future__ import annotations


from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator

from app.schemas.common import BaseSchema, validate_email


# =============================================================================
# LOGIN
# =============================================================================

class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: str = Field(
        min_length=1,
        max_length=255,
        description="User email address",
    )
    
    password: str = Field(
        min_length=1,
        max_length=255,
        description="User password",
    )
    
    _validate_email = validator("email", allow_reuse=True)(validate_email)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "email": "besiktningsman@example.com",
                "password": "secure_password_123"
            }
        }


class TokenResponse(BaseModel):
    """Token response schema."""
    
    access_token: str = Field(
        description="JWT access token",
    )
    
    token_type: str = Field(
        default="Bearer",
        description="Token type (always 'Bearer')",
    )
    
    expires_in: int = Field(
        description="Token expiration time in seconds",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class UserProfile(BaseSchema):
    """User profile schema."""
    
    id: int = Field(
        description="User ID",
    )
    
    email: str = Field(
        description="Email address",
    )
    
    name: str = Field(
        description="Full name",
    )
    
    role: str = Field(
        description="User role (admin, inspector, viewer)",
    )
    
    active: bool = Field(
        description="Whether the account is active",
    )
    
    company_name: Optional[str] = Field(
        default=None,
        description="Company name",
    )
    
    certification_org: Optional[str] = Field(
        default=None,
        description="Certifieringsorgan",
    )
    
    certification_number: Optional[str] = Field(
        default=None,
        description="Certifieringsnummer",
    )
    
    certification_valid_until: Optional[str] = Field(
        default=None,
        description="Giltighetstid",
    )
    
    competence: Optional[str] = Field(
        default=None,
        description="Behörighet",
    )
    
    phone: Optional[str] = Field(
        default=None,
        description="Phone number",
    )
    
    signature_image_id: Optional[str] = Field(
        default=None,
        description="Signature image reference",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "besiktningsman@example.com",
                "name": "Erik Andersson",
                "role": "inspector",
                "active": True,
                "company_name": "Besiktningsfirman AB",
                "certification_org": "SP",
                "certification_number": "12345",
                "certification_valid_until": "2026-12-31",
                "competence": "OVK",
                "phone": "+46701234567",
                "signature_image_id": None
            }
        }


class LoginResponse(BaseModel):
    """Login response schema."""
    
    data: dict = Field(
        description="Response data containing tokens and user info",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": 1,
                        "email": "besiktningsman@example.com",
                        "name": "Erik Andersson",
                        "role": "inspector"
                    }
                }
            }
        }


# =============================================================================
# USER MANAGEMENT (for future expansion)
# =============================================================================

class UserCreate(BaseModel):
    """User creation schema (admin only)."""
    
    email: str = Field(
        min_length=1,
        max_length=255,
        description="Email address",
    )
    
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password (min 8 characters)",
    )
    
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Full name",
    )
    
    role: str = Field(
        default="inspector",
        pattern="^(admin|inspector|viewer)$",
        description="User role",
    )
    
    _validate_email = validator("email", allow_reuse=True)(validate_email)


class UserUpdate(BaseModel):
    """User update schema."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Full name",
    )
    
    company_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Company name",
    )
    
    certification_org: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Certifieringsorgan",
    )
    
    certification_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Certifieringsnummer",
    )
    
    certification_valid_until: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Giltighetstid",
    )
    
    competence: Optional[str] = Field(
        default=None,
        description="Behörighet",
    )
    
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Phone number",
    )


class PasswordChange(BaseModel):
    """Password change schema."""
    
    current_password: str = Field(
        min_length=1,
        description="Current password",
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password (min 8 characters)",
    )
