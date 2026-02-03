from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - PDF SCHEMAS
=============================================================================
Pydantic schemas for PDF generation and versioning.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin, PaginationMeta


# =============================================================================
# PDF GENERATION
# =============================================================================

class PDFGenerateRequest(BaseModel):
    """PDF generation request."""
    
    inspection_id: int = Field(
        description="Inspection ID to generate PDF for",
    )
    
    status: str = Field(
        default="draft",
        pattern="^(draft|final)$",
        description="PDF status: draft or final",
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional PDF generation options",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "inspection_id": 1,
                "status": "draft",
                "options": {
                    "include_images": True,
                    "sort_apartments": True
                }
            }
        }


class PDFGenerateResponse(BaseModel):
    """PDF generation response."""
    
    data: Dict[str, Any] = Field(
        description="Generated PDF metadata",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {
                    "id": 1,
                    "version_number": 1,
                    "status": "draft",
                    "url": "https://storage/pdfs/inspection_1_v1.pdf",
                    "filename": "besiktning_1_v1.pdf",
                    "size_bytes": 524288,
                    "checksum": "sha256:abc123...",
                    "created_at": "2026-01-29T12:00:00Z"
                }
            }
        }


# =============================================================================
# PDF VERSION
# =============================================================================

class PDFVersionResponse(BaseSchema, TimestampMixin):
    """PDF version response."""
    
    id: int = Field(
        description="PDF version ID",
    )
    
    inspection_id: int = Field(
        description="Inspection ID",
    )
    
    version_number: int = Field(
        description="Version number (1, 2, 3...)",
    )
    
    status: str = Field(
        description="Status: draft or final",
    )
    
    storage_key: str = Field(
        description="Storage key/path",
    )
    
    filename: str = Field(
        description="Filename",
    )
    
    size_bytes: int = Field(
        description="File size in bytes",
    )
    
    checksum: str = Field(
        description="SHA256 checksum",
    )
    
    created_by_user_id: Optional[int] = Field(
        description="User who created this version",
    )
    
    url: Optional[str] = Field(
        default=None,
        description="Access URL (may be presigned)",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "inspection_id": 1,
                "version_number": 1,
                "status": "draft",
                "storage_key": "pdfs/2026/01/inspection_1_v1.pdf",
                "filename": "besiktning_1_v1.pdf",
                "size_bytes": 524288,
                "checksum": "sha256:abc123...",
                "created_by_user_id": 1,
                "url": "https://storage/pdfs/inspection_1_v1.pdf",
                "created_at": "2026-01-29T12:00:00Z",
                "updated_at": "2026-01-29T12:00:00Z"
            }
        }


class PDFVersionList(BaseModel):
    """PDF version list response."""
    
    data: List[PDFVersionResponse] = Field(
        description="List of PDF versions",
    )
    
    meta: Optional[PaginationMeta] = Field(
        default=None,
        description="Pagination metadata",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": 3,
                        "version_number": 3,
                        "status": "final",
                        "created_at": "2026-01-29T14:00:00Z"
                    },
                    {
                        "id": 2,
                        "version_number": 2,
                        "status": "draft",
                        "created_at": "2026-01-29T13:00:00Z"
                    },
                    {
                        "id": 1,
                        "version_number": 1,
                        "status": "draft",
                        "created_at": "2026-01-29T12:00:00Z"
                    }
                ],
                "meta": {
                    "total": 3,
                    "limit": 20,
                    "offset": 0,
                    "has_more": False
                }
            }
        }


# =============================================================================
# PDF OPTIONS
# =============================================================================

class PDFOptions(BaseModel):
    """PDF generation options."""
    
    include_images: bool = Field(
        default=True,
        description="Include defect images in PDF",
    )
    
    sort_apartments: bool = Field(
        default=True,
        description="Sort apartments numerically",
    )
    
    include_measurements: bool = Field(
        default=True,
        description="Include measurement data",
    )
    
    include_summary: bool = Field(
        default=True,
        description="Include summary page",
    )
    
    page_size: str = Field(
        default="A4",
        pattern="^(A4|Letter)$",
        description="Page size: A4 or Letter",
    )
    
    language: str = Field(
        default="sv",
        pattern="^(sv|en)$",
        description="Language: sv (Swedish) or en (English)",
    )
