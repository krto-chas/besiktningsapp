from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - PROPERTY SCHEMAS
=============================================================================
Pydantic schemas for Property (Fastighet) operations.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    BaseSchema,
    TimestampMixin,
    RevisionMixin,
    ClientIdMixin,
    PaginationMeta,
)


# =============================================================================
# PROPERTY SCHEMAS
# =============================================================================

class PropertyCreate(BaseModel):
    """Property creation schema."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client-generated UUID (optional)",
    )
    
    property_type: str = Field(
        min_length=1,
        max_length=100,
        description="Type: flerbostadshus, villa, kontor, etc.",
    )
    
    designation: str = Field(
        min_length=1,
        max_length=255,
        description="Fastighetsbeteckning",
    )
    
    owner: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Property owner name",
    )
    
    address: str = Field(
        min_length=1,
        max_length=500,
        description="Street address",
    )
    
    postal_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Postal code",
    )
    
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City",
    )
    
    num_apartments: Optional[int] = Field(
        default=None,
        ge=0,
        le=10000,
        description="Number of apartments",
    )
    
    num_premises: Optional[int] = Field(
        default=None,
        ge=0,
        le=10000,
        description="Number of premises",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Additional notes",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "property_type": "flerbostadshus",
                "designation": "STOCKHOLM 1:1",
                "owner": "Fastighetsägare AB",
                "address": "Exempelgatan 123",
                "postal_code": "11122",
                "city": "Stockholm",
                "num_apartments": 24,
                "num_premises": 2,
                "notes": "Byggd 1975"
            }
        }


class PropertyUpdate(BaseModel):
    """Property update schema."""
    
    base_revision: int = Field(
        ge=1,
        description="Current revision (for optimistic locking)",
    )
    
    property_type: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Property type",
    )
    
    designation: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Fastighetsbeteckning",
    )
    
    owner: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Owner name",
    )
    
    address: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Address",
    )
    
    postal_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Postal code",
    )
    
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City",
    )
    
    num_apartments: Optional[int] = Field(
        default=None,
        ge=0,
        le=10000,
        description="Number of apartments",
    )
    
    num_premises: Optional[int] = Field(
        default=None,
        ge=0,
        le=10000,
        description="Number of premises",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Notes",
    )


class PropertyResponse(BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin):
    """Property response schema."""
    
    id: int = Field(
        description="Property ID",
    )
    
    property_type: str = Field(
        description="Property type",
    )
    
    designation: str = Field(
        description="Fastighetsbeteckning",
    )
    
    owner: Optional[str] = Field(
        description="Owner name",
    )
    
    address: str = Field(
        description="Address",
    )
    
    postal_code: Optional[str] = Field(
        description="Postal code",
    )
    
    city: Optional[str] = Field(
        description="City",
    )
    
    num_apartments: Optional[int] = Field(
        description="Number of apartments",
    )
    
    num_premises: Optional[int] = Field(
        description="Number of premises",
    )
    
    notes: Optional[str] = Field(
        description="Notes",
    )


class PropertyList(BaseModel):
    """Property list response schema."""
    
    data: List[PropertyResponse] = Field(
        description="List of properties",
    )
    
    meta: Optional[PaginationMeta] = Field(
        default=None,
        description="Pagination metadata",
    )
