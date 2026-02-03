from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - DEFECT SCHEMAS
=============================================================================
Pydantic schemas for Defect (Felrapport) operations.
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
# DEFECT PHOTO SCHEMA
# =============================================================================

class DefectPhotoSchema(BaseModel):
    """Photo reference for defect creation."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client UUID for photo",
    )
    
    image_id: Optional[int] = Field(
        default=None,
        description="Image ID (if already uploaded)",
    )
    
    storage_key: Optional[str] = Field(
        default=None,
        description="Storage key (if uploaded)",
    )
    
    filename_hint: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Filename hint (e.g., A12_kok_20260129.jpg)",
    )


# =============================================================================
# DEFECT SCHEMAS
# =============================================================================

class DefectCreate(BaseModel):
    """Defect creation schema."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client-generated UUID",
    )
    
    apartment_id: Optional[int] = Field(
        default=None,
        description="Apartment ID (server reference)",
    )
    
    apartment_client_id: Optional[str] = Field(
        default=None,
        description="Apartment client ID (for offline)",
    )
    
    room_index: int = Field(
        ge=0,
        le=9999,
        description="Room index within apartment",
    )
    
    code: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Standard defect code (e.g., VF01)",
    )
    
    title: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Short title",
    )
    
    description: str = Field(
        min_length=1,
        max_length=2000,
        description="Detailed description (required)",
    )
    
    remedy: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Recommended remedy",
    )
    
    severity: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
        description="Severity: low, medium, high",
    )
    
    photos: List[DefectPhotoSchema] = Field(
        default_factory=list,
        max_items=20,
        description="Photo references (max 20)",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "apartment_id": 1,
                "room_index": 1,
                "code": "VF01",
                "description": "Ventil saknas i köket",
                "remedy": "Installera från-luftsventil",
                "severity": "high",
                "photos": []
            }
        }


class DefectUpdate(BaseModel):
    """Defect update schema."""
    
    base_revision: int = Field(
        ge=1,
        description="Current revision",
    )
    
    room_index: Optional[int] = Field(
        default=None,
        ge=0,
        le=9999,
        description="Room index",
    )
    
    code: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Defect code",
    )
    
    title: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Title",
    )
    
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description="Description",
    )
    
    remedy: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Remedy",
    )
    
    severity: Optional[str] = Field(
        default=None,
        pattern="^(low|medium|high)$",
        description="Severity",
    )


class DefectResponse(BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin):
    """Defect response schema."""
    
    id: int = Field(description="Defect ID")
    apartment_id: int = Field(description="Apartment ID")
    room_index: int = Field(description="Room index")
    code: Optional[str] = Field(description="Code")
    title: Optional[str] = Field(description="Title")
    description: str = Field(description="Description")
    remedy: Optional[str] = Field(description="Remedy")
    severity: str = Field(description="Severity")
    photos: List[dict] = Field(default_factory=list, description="Photo metadata")


class DefectList(BaseModel):
    """Defect list response schema."""
    
    data: List[DefectResponse] = Field(description="List of defects")
    meta: Optional[PaginationMeta] = Field(default=None, description="Pagination metadata")
