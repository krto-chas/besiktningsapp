"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTION SCHEMAS
=============================================================================
Pydantic schemas for Inspection (Besiktning) operations.
"""
from __future__ import annotations


from typing import List, Optional
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import (
    BaseSchema,
    TimestampMixin,
    RevisionMixin,
    ClientIdMixin,
    PaginationMeta,
)


# =============================================================================
# INSPECTION SCHEMAS
# =============================================================================

class InspectionCreate(BaseModel):
    """Inspection creation schema."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client-generated UUID (optional)",
    )
    
    property_id: Optional[int] = Field(
        default=None,
        description="Property ID (server-side reference)",
    )
    
    property_client_id: Optional[str] = Field(
        default=None,
        description="Property client ID (for offline creation)",
    )
    
    date: date = Field(
        description="Inspection date",
    )
    
    active_time_seconds: int = Field(
        default=0,
        ge=0,
        le=86400,
        description="Active time in seconds (max 24h)",
    )
    
    status: str = Field(
        default="draft",
        pattern="^(draft|final|archived)$",
        description="Status: draft, final, or archived",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="General notes",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "property_id": 1,
                "date": "2026-01-29",
                "active_time_seconds": 7200,
                "status": "draft",
                "notes": "OVK-besiktning"
            }
        }


class InspectionUpdate(BaseModel):
    """Inspection update schema."""
    
    base_revision: int = Field(
        ge=1,
        description="Current revision for optimistic locking",
    )
    
    date: Optional[date] = Field(
        default=None,
        description="Inspection date",
    )
    
    active_time_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        le=86400,
        description="Active time in seconds",
    )
    
    status: Optional[str] = Field(
        default=None,
        pattern="^(draft|final|archived)$",
        description="Status",
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Notes",
    )


class InspectionResponse(BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin):
    """Inspection response schema."""
    
    id: int = Field(
        description="Inspection ID",
    )
    
    property_id: int = Field(
        description="Property ID",
    )
    
    inspector_id: Optional[int] = Field(
        description="Inspector user ID",
    )
    
    date: date = Field(
        description="Inspection date",
    )
    
    active_time_seconds: int = Field(
        description="Active time in seconds",
    )
    
    status: str = Field(
        description="Status: draft, final, or archived",
    )
    
    notes: Optional[str] = Field(
        description="Notes",
    )


class InspectionList(BaseModel):
    """Inspection list response schema."""
    
    data: List[InspectionResponse] = Field(
        description="List of inspections",
    )
    
    meta: Optional[PaginationMeta] = Field(
        default=None,
        description="Pagination metadata",
    )
