"""
=============================================================================
BESIKTNINGSAPP BACKEND - IMAGE SCHEMAS
=============================================================================
Pydantic schemas for image upload and metadata.
"""
from __future__ import annotations


from typing import Optional, Dict
from pydantic import BaseModel, Field


class ImageUploadRequest(BaseModel):
    """Direct image upload request (multipart)."""
    defect_id: Optional[int] = Field(default=None, description="Defect ID (server)")
    defect_client_id: Optional[str] = Field(default=None, description="Defect client ID")
    filename_hint: Optional[str] = Field(default=None, max_length=255, description="Filename hint")


class PresignedUploadRequest(BaseModel):
    """Presigned URL request."""
    purpose: str = Field(default="image", description="Purpose: image or pdf")
    content_type: str = Field(description="Content type (e.g., image/jpeg)")
    filename: str = Field(max_length=255, description="Filename")
    size_bytes: int = Field(gt=0, le=10485760, description="File size in bytes (max 10MB)")
    
    class Config:
        json_schema_extra = {"example": {"purpose": "image", "content_type": "image/jpeg", "filename": "photo.jpg", "size_bytes": 123456}}


class PresignedUploadResponse(BaseModel):
    """Presigned URL response."""
    data: Dict[str, str] = Field(description="Upload URL and metadata")
    
    class Config:
        json_schema_extra = {"example": {"data": {"upload_url": "https://...", "storage_key": "...", "expires_at": "..."}}}


class ImageCompleteRequest(BaseModel):
    """Complete image upload request."""
    storage_key: str = Field(max_length=500, description="Storage key")
    defect_id: Optional[int] = Field(default=None, description="Defect ID")
    defect_client_id: Optional[str] = Field(default=None, description="Defect client ID")
    checksum: str = Field(max_length=64, description="SHA256 checksum")


class ImageResponse(BaseModel):
    """Image metadata response."""
    data: Dict = Field(description="Image metadata")
    
    class Config:
        json_schema_extra = {"example": {"data": {"id": 1, "url": "https://...", "filename": "photo.jpg", "size_bytes": 123456}}}
