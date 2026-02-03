from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - APARTMENT SCHEMAS
=============================================================================
Pydantic schemas for Apartment and Room operations.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.common import (
    BaseSchema,
    TimestampMixin,
    RevisionMixin,
    ClientIdMixin,
    PaginationMeta,
    validate_apartment_number,
)


# =============================================================================
# ROOM SCHEMA
# =============================================================================

class RoomSchema(BaseModel):
    """Room schema (for JSON field in Apartment)."""
    
    index: int = Field(
        ge=0,
        le=9999,
        description="Room index (0-based, unique within apartment)",
    )
    
    type: str = Field(
        min_length=1,
        max_length=50,
        description="Room type: hall, kok, sovrum, vardagsrum, badrum, etc.",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "index": 1,
                "type": "kok"
            }
        }


# =============================================================================
# APARTMENT SCHEMAS
# =============================================================================

class ApartmentCreate(BaseModel):
    """Apartment creation schema."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client-generated UUID (optional)",
    )
    
    inspection_id: Optional[int] = Field(
        default=None,
        description="Inspection ID (server reference)",
    )
    
    inspection_client_id: Optional[str] = Field(
        default=None,
        description="Inspection client ID (for offline)",
    )
    
    apartment_number: str = Field(
        min_length=1,
        max_length=20,
        description="Apartment number (e.g., 1201, A12, 12B)",
    )
    
    rooms: List[RoomSchema] = Field(
        default_factory=list,
        max_items=50,
        description="List of rooms",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes",
    )
    
    _validate_number = validator("apartment_number", allow_reuse=True)(validate_apartment_number)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "inspection_id": 1,
                "apartment_number": "1201",
                "rooms": [
                    {"index": 0, "type": "hall"},
                    {"index": 1, "type": "kok"},
                    {"index": 2, "type": "sovrum"},
                ],
                "notes": "3 rum och kök"
            }
        }


class ApartmentUpdate(BaseModel):
    """Apartment update schema."""
    
    base_revision: int = Field(
        ge=1,
        description="Current revision for optimistic locking",
    )
    
    apartment_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Apartment number",
    )
    
    rooms: Optional[List[RoomSchema]] = Field(
        default=None,
        max_items=50,
        description="Rooms list",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes",
    )
    
    _validate_number = validator("apartment_number", allow_reuse=True)(validate_apartment_number)


class ApartmentResponse(BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin):
    """Apartment response schema."""
    
    id: int = Field(
        description="Apartment ID",
    )
    
    inspection_id: int = Field(
        description="Inspection ID",
    )
    
    apartment_number: str = Field(
        description="Apartment number",
    )
    
    rooms: List[RoomSchema] = Field(
        description="List of rooms",
    )
    
    notes: Optional[str] = Field(
        description="Notes",
    )


class ApartmentList(BaseModel):
    """Apartment list response schema."""
    
    data: List[ApartmentResponse] = Field(
        description="List of apartments",
    )
    
    meta: Optional[PaginationMeta] = Field(
        default=None,
        description="Pagination metadata",
    )
